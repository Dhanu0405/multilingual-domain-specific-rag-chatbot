# Voice-Enabled Multilingual RAG Chatbot

An advanced, fully localized Retrieval-Augmented Generation (RAG) system running locally on your hardware. This chatbot digests your PDF/DOCX/TXT files into a vector database and allows you to chat with them natively using your voice in multiple languages (English, Hindi, Spanish).

## Prerequisites
Before you start, make sure you have the following installed on your machine:
- **Python 3.9+**
- **Node.js 18+**
- **FFmpeg** (Required by Whisper for Audio Transcription to work natively)
- **Ollama** (Running locally on your machine)

You will need the Llama 3.2 3B model. Once Ollama is installed, run this command in your terminal to download the brain:
```bash
ollama run llama3.2:3b
```


## 1. Backend Setup (FastAPI / LlamaIndex)

The backend handles document ingestion, chromaDB embedding, translations, and generating text-to-speech audio files locally.

1. Open a terminal and navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment to isolate the python packages:
```bash
# On Windows
python -m venv venv
```

3. Activate the virtual environment:
```bash
# On Windows PowerShell
.\venv\Scripts\Activate
```

4. Install all the required AI models and backend dependencies:
```bash
pip install -r requirements.txt
```

5. Start the backend server:
```bash
uvicorn main:app --reload
```
*(The backend will now be running on `http://localhost:8000`)*


## 2. Frontend Setup (React / Vite)

The frontend contains a modern, glassmorphic UI integrated with the Web Audio MediaRecorder APIs for streaming voice.

1. Open a **new, separate** terminal window and navigate to the frontend directory:
```bash
cd frontend
```

2. Install the necessary Node packages:
```bash
npm install
```

3. Start the Vite development server:
```bash
npm run dev
```
*(The frontend will now be running on `http://localhost:5173`)*

## 3. Usage
Simply open your browser to `http://localhost:5173`. 
1. Use the sidebar to upload a PDF or Text file.
2. Type a question or click the **Microphone** icon to ask a question naturally in English, Hindi, or Spanish.
3. The chatbot will translate your voice, ingest the document semantics, and literally speak the response back to you via the resulting "Listen" button interface!
