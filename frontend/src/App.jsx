import React, { useState, useEffect } from 'react';
import './App.css';
import VoiceRecorder from './components/VoiceRecorder';
import AudioPlayer from './components/AudioPlayer';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputStr, setInputStr] = useState("");
  const [files, setFiles] = useState([]);
  const [uploadStatus, setUploadStatus] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch("http://localhost:8000/files")
      .then(res => res.json())
      .then(data => {
        if(data.files) setFiles(data.files);
      })
      .catch(console.error);
  }, []);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setFiles([...files, file.name]);
    setUploadStatus("Uploading...");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        setUploadStatus("Ingesting...");
        fetch("http://localhost:8000/files").then(r => r.json()).then(d => d.files && setFiles(d.files));
        const ingestRes = await fetch("http://localhost:8000/ingest", {
          method: "POST"
        });
        if(ingestRes.ok) {
           setUploadStatus("Indexed!");
        } else {
           setUploadStatus("Indexed Error.");
        }
      }
    } catch(err) {
      setUploadStatus("Upload Failed");
    }
    
    setTimeout(() => setUploadStatus(""), 3000);
  };

  const handleSendMessage = async () => {
    if (!inputStr.trim()) return;

    const userMsg = { sender: 'user', text: inputStr };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);
    setInputStr("");

    try {
      const res = await fetch("http://localhost:8000/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: userMsg.text }),
      });
      
      const data = await res.json();
      const botMsg = { 
        sender: 'bot', 
        text: data.response, 
        lang: data.detected_language || "en",
        sources: data.sources,
        audioUrl: data.audio_url
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch(err) {
      setMessages((prev) => [...prev, { sender: 'error', text: "Failed to fetch response." }]);
    }
    setLoading(false);
  };

  return (
    <div className="dashboard-container">
      <div className="sidebar">
        <h2 className="title">Knowledge Base</h2>
        
        <div className="upload-container">
          <label className="upload-btn">
             + Upload Document
             <input type="file" onChange={handleFileUpload} accept=".pdf,.txt,.docx" hidden />
          </label>
          <span className="status-text">{uploadStatus}</span>
        </div>

        <div className="file-list">
           <h3>Indexed Files</h3>
           {files.length === 0 ? <p className="empty-text">No files uploaded yet.</p> : null}
           {files.map((f, i) => (
             <div key={i} className="file-item">📁 {f}</div>
           ))}
        </div>
      </div>

      <div className="chat-area">
        <div className="chat-header">
           <h2>AI RAG Assistant</h2>
           <p>Powered by local LLM & ChromaDB</p>
        </div>
        
        <div className="messages-view">
           {messages.length === 0 && (
              <div className="welcome">
                 Ask a question about your uploaded documents!
              </div>
           )}
           {messages.map((m, i) => (
             <div key={i} className={`message-wrapper ${m.sender}`}>
               <div className="message-bubble">
                  {m.text}
               </div>
               
               {m.sender === 'bot' && (
                 <div className="message-actions">
                    <AudioPlayer text={m.text} lang={m.lang} audioUrl={m.audioUrl} />
                    <span className="source-badge lang-badge">{m.lang ? m.lang.toUpperCase() : 'EN'}</span>
                    {m.sources && <span className="source-badge">{m.sources}</span>}
                 </div>
               )}
             </div>
           ))}
           {loading && <div className="loading-dot">...</div>}
        </div>

        <div className="input-area">
          <VoiceRecorder onTranscriptionComplete={(text) => setInputStr(text)} />
          <input 
            type="text" 
            placeholder="Ask anything or click the mic to speak..." 
            value={inputStr}
            onChange={(e) => setInputStr(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSendMessage()}
          />
          <button onClick={handleSendMessage} disabled={loading}>Send</button>
        </div>
      </div>
    </div>
  );
}

export default App;
