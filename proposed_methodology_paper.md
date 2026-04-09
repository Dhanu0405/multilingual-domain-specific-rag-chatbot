\section{Proposed Methodology}

This section outlines the architectural design and implementation strategy for the proposed domain-specific conversational agent. The methodology is structured to support secure, localized execution without relying on external cloud APIs, ensuring data privacy and low-latency inference. The system integrates advanced retrieval-augmented generation methodologies alongside specialized multilingual and acoustic processing modules, establishing a comprehensive end-to-end framework for interactive knowledge extraction.

\subsection{Dataset Preparation}

In contrast to traditional machine learning paradigms that necessitate extensive annotated datasets for model training, the proposed RAG architecture is fundamentally designed to operate on unstructured, user-provided domain documents directly. Consequently, intensive dataset preparation and conventional manual labeling are rendered unnecessary. The system accommodates dynamic academic artifacts such as Portable Document Format (PDF) files, Microsoft Word documents (DOCX), and raw text files (TXT). The preprocessing pipeline is therefore strictly limited to automated text extraction and recursive semantic chunking. This minimal preprocessing approach ensures that raw academic notes are rapidly transformed into machine-readable embeddings with overlapping tokens to preserve contextual boundaries, facilitating real-time ingestion without imposing prohibitive computational overhead on the user.

\subsection{Model Architecture}

The core architecture of the proposed system is bifurcated into two primary operational domains: the retrieval infrastructure and the generative language model engine.

\subsubsection{Retrieval-Augmented Generation (RAG) System Architecture}

The pipeline initiates with a robust document ingestion phase, where parsed textual data undergoes recursive chunking to optimally fit within the subsequent encoding limitations. The system employs the \textit{all-MiniLM-L6-v2} sentence-transformer model to systematically project these text chunks into dense, high-dimensional vector embeddings. These semantic embeddings are subsequently persisted within ChromaDB, a localized, highly optimized vector database that enables rapid nearest-neighbor similarity searches. Upon receiving a user query, the retriever isolates the top-$k$ most contextually relevant semantic chunks from the vector database. These retrieved nodes are then systematically fused with the original query and forwarded to the generative engine to orchestrate an informed response. 

\begin{figure}[h]
\centering
% Insert RAG architecture diagram here
\caption{Overall architecture of the proposed local Retrieval-Augmented Generation pipeline.}
\end{figure}

\subsubsection{Large Language Model Specifications}

The generative capabilities of the system are driven by the highly optimized Llama 3.2 model, specifically utilizing the 3-billion parameter variant. The selection of a 3B parameter model represents a deliberate architectural trade-off between semantic depth and computational frugality. Due to its lightweight parameter footprint, the model demonstrates exceptional suitability for on-premise, localized deployment without necessitating specialized, high-tier graphics processing units. This localized execution strategy effectively mitigates the network latency inherently associated with cloud-based API calls, thereby yielding high-efficiency, near real-time generative throughput critical for seamless conversational interfaces.

\begin{figure}[h]
\centering
% Insert Llama 3.2 3B architecture diagram here
\caption{Architectural overview of the Llama 3.2 3B inference model.}
\end{figure}

\subsection{System Pipeline and Grounding Strategy}

Due to the fundamental nature of the RAG paradigm, traditional gradient descent-based fine-tuning is circumvented. Instead, the system leverages a dynamic, retrieval-based grounding strategy to anchor the generative language model to the specific academic context. The operational flow commences by projecting the live user query through the identical embedding space used during domain ingestion. A cosine similarity search isolates the most pertinent factual chunks within the immediate operational context. Subsequently, these chunks undergo stringent context injection via a highly rigid prompt design. To aggressively mitigate generative hallucination, the system enforces a strict operational constraint through system prompting, explicitly instructing the model to synthesize answers exclusively from the retrieved context matrices. If the generative engine determines that the provided vectors lack sufficient evidentiary support, it is constrained to output a deterministically safe failure response.

\subsection{Voice and Multilingual Integration}

To democratize user accessibility, the architecture is significantly expanded by an integrated acoustic-multilingual routing layer. Acoustic inputs are intercepted and locally decoded via the Whisper automatic speech recognition model (utilizing the structurally optimized \textit{faster-whisper} implementation), which executes highly accurate speech-to-text transcriptions natively. Following transcription, a dedicated language detection module extrapolates the phonetic and syntactic origin of the string. To maximize the semantic retrieval accuracy of the backing framework—which exhibits peak performance indices within English linguistic spaces—all non-English queries undergo localized algorithmic translation to English prior to vector search execution. The grounded English response synthesized by the underlying model is subsequently reverse-translated into the user's natively detected language. Finally, the text-to-speech synthesis engine, driven by the \textit{gTTS} framework, compiles the translated text response back into an acoustic auditory stream. This tightly coupled integration ensures a frictionless, fully localized conversational loop accommodating heterogeneous linguistic and auditory parameters.
