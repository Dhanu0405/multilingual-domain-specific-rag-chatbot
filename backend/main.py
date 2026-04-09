import os
import shutil
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings, PromptTemplate
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.ollama import Ollama
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from voice.speech_to_text import transcribe_audio
from voice.language_detection import detect_language
from voice.text_to_speech import generate_speech
from deep_translator import GoogleTranslator

app = FastAPI(title="RAG Chatbot API", description="Full RAG Pipeline added with Voice.")

# Allow React app on localhost:5173 to communicate with the Backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

CHROMA_DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
os.makedirs(CHROMA_DB_DIR, exist_ok=True)

# Serve uploads directory so frontend can play audio natively via URL
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# LlamaIndex Settings
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
Settings.llm = Ollama(
    model="llama3.2:3b", 
    request_timeout=360.0,
    context_window=2048,
    additional_kwargs={"num_ctx": 2048}
)

@app.on_event("startup")
async def startup_event():
    # Clean up old TTS mp3 files on session startup to prevent clutter
    if os.path.exists(UPLOAD_DIR):
        for f in os.listdir(UPLOAD_DIR):
            if f.startswith("tts_response_") and f.endswith(".mp3"):
                try:
                    os.remove(os.path.join(UPLOAD_DIR, f))
                except Exception:
                    pass

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI backend!"}

@app.get("/test")
async def test_route():
    return {"status": "success", "message": "Backend Foundation is successfully set up!"}

@app.get("/files")
async def list_files():
    try:
        files = []
        if os.path.exists(UPLOAD_DIR):
            # Only return actual document files, hide TTS mp3s and temp files
            for f in os.listdir(UPLOAD_DIR):
                if not (f.startswith("tts_response_") or f.startswith("temp_") or f.endswith(".mp3")):
                    files.append(f)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "saved_path": file_path, "message": "File uploaded successfully"}

@app.post("/speech-to-text")
async def process_speech_to_text(file: UploadFile = File(...)):
    try:
        # Save audio file temporarily
        temp_audio_path = os.path.join(UPLOAD_DIR, f"temp_{file.filename}")
        with open(temp_audio_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Transcribe audio
        transcribed_text = transcribe_audio(temp_audio_path)
        
        # Clean up temporary file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
            
        return {"text": transcribed_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT Error: {str(e)}")

class TTSRequest(BaseModel):
    text: str
    lang: str = "en"

@app.post("/text-to-speech")
async def process_text_to_speech(request: TTSRequest):
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty.")
            
        # Creating a safe and somewhat unique filename using python's built-in hash
        safe_hash = abs(hash(request.text))
        output_filename = f"tts_response_{safe_hash}.mp3"
        output_path = os.path.join(UPLOAD_DIR, output_filename)
        
        generate_speech(request.text, request.lang, output_path)
        
        # Return the actual audio file binary
        return FileResponse(output_path, media_type="audio/mpeg", filename=output_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS Error: {str(e)}")

@app.post("/ingest")
async def ingest_documents():
    if not os.path.exists(UPLOAD_DIR) or not os.listdir(UPLOAD_DIR):
        raise HTTPException(status_code=400, detail="No files to ingest. Please upload files first.")
        
    try:
        # 1. Extract text from uploaded documents (PDF, PPT, DOCX, TXT)
        reader = SimpleDirectoryReader(input_dir=UPLOAD_DIR, required_exts=[".pdf", ".docx", ".txt"])
        documents = reader.load_data()
        
        # 2. Implement recursive chunking
        # Using LlamaIndex's SentenceSplitter for recursive chunking
        text_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        
        # 3. Generate chunks (nodes) from documents
        nodes = text_parser.get_nodes_from_documents(documents)
        
        # 4. Generate embeddings and store in persistent ChromaDB
        db = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        chroma_collection = db.get_or_create_collection("rag_collection")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Build Vector Index (will automatically create/save embeddings to Chroma)
        index = VectorStoreIndex(nodes, storage_context=storage_context)
        
        # Capture sample preview 
        first_chunk_text = nodes[0].text if nodes else ""
        
        return {
            "message": "Ingestion, Chunking, and Embedding successful!",
            "documents_processed": len(documents),
            "chunks_generated": len(nodes),
            "vector_db": "ChromaDB Persistent",
            "sample_chunk": first_chunk_text[:300] + "..." if first_chunk_text else ""
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during ingestion: {str(e)}")

class QueryRequest(BaseModel):
    query: str

@app.post("/retrieve")
async def retrieve_chunks(request: QueryRequest):
    try:
        # Connect to ChromaDB
        db = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        chroma_collection = db.get_or_create_collection("rag_collection")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        
        # Load index from existing vector store
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        
        # Setup retriever for top 5 chunks
        retriever = index.as_retriever(similarity_top_k=5)
        
        # Retrieve nodes based on user query
        retrieved_nodes = retriever.retrieve(request.query)
        
        # Format the results
        results = []
        for i, node in enumerate(retrieved_nodes):
            results.append({
                "chunk_index": i + 1,
                "score": node.score,
                "text": node.text
            })
            
        return {
            "query": request.query,
            "retrieved_count": len(retrieved_nodes),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during retrieval: {str(e)}")

class GenerateRequest(BaseModel):
    prompt: str

@app.post("/generate")
async def generate_response(request: GenerateRequest):
    try:
        response = Settings.llm.complete(request.prompt)
        return {"response": str(response)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")

# Prepare strict QA template instruction 
qa_prompt_tmpl_str = (
    "Context information is below.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "Answer ONLY from the provided context. If the answer is not present, say: 'I don’t know based on the provided documents.'\n"
    "Query: {query_str}\n"
    "Answer: "
)
qa_prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)

@app.post("/query")
async def query_rag(request: QueryRequest):
    try:
        # Load the Chroma DB Database
        db = chromadb.PersistentClient(path=CHROMA_DB_DIR)
        chroma_collection = db.get_or_create_collection("rag_collection")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        
        # Combine the Vector Retriever with the LLM 
        query_engine = index.as_query_engine(
            similarity_top_k=5,
            text_qa_template=qa_prompt_tmpl
        )
        
        # Phase 4: Detect and Translate Query
        original_query = request.query
        lang = detect_language(original_query)
        print(f"\n--- New Query ---", flush=True)
        print(f"Detected language: {lang}", flush=True)
        
        search_query = original_query
        if lang != "en":
            try:
                search_query = GoogleTranslator(source='auto', target='en').translate(original_query)
                print(f"Translated query ({lang} -> en): {search_query}", flush=True)
            except Exception as e:
                print(f"Translation to English failed: {e}", flush=True)
        
        # Querying fires semantic search THEN sends context + prompt to the LLM automatically
        response = query_engine.query(search_query)
        response_text = str(response)

        # Phase 4: Translate Response back to original language
        if lang != "en":
            try:
                translated_resp = GoogleTranslator(source='en', target=lang).translate(response_text)
                print(f"Translated response (en -> {lang}): {translated_resp}", flush=True)
                response_text = translated_resp
            except Exception as e:
                print(f"Translation back to {lang} failed: {e}", flush=True)
        
        # Phase 8: Source Attribution (Improved Dynamic Filtering)
        source_files = set()
        if response.source_nodes:
            # Find the highest semantic match score among the 5 retrieved chunks
            max_score = max((node.score for node in response.source_nodes if node.score is not None), default=0)
            
            for node in response.source_nodes:
                file_name = node.metadata.get('file_name')
                # Only attribute the file if its chunk's score is within 70% of the best matching chunk
                # (This drops irrelevant files that were just pulled in to fill the top_k=5 quota)
                if file_name and (node.score is None or node.score >= max_score * 0.7):
                    source_files.add(file_name)
        
        sources_str = ", ".join(source_files) if source_files else "Unknown"
        attribution = f"Answer generated from: {sources_str}"
        
        # Phase 7: Full integration - generate audio right inside the RAG flow
        unique_id = uuid.uuid4().hex
        audio_filename = f"tts_response_{unique_id}.mp3"
        audio_path = os.path.join(UPLOAD_DIR, audio_filename)
        generate_speech(response_text, lang, audio_path)
        audio_url = f"http://localhost:8000/uploads/{audio_filename}"
        
        return {
            "query": request.query,
            "detected_language": lang,
            "response": response_text,
            "sources": attribution,
            "audio_url": audio_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in RAG computation: {str(e)}")
