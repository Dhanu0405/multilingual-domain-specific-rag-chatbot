import React, { useState, useRef } from 'react';

const VoiceRecorder = ({ onTranscriptionComplete }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      
      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        audioChunksRef.current = []; // Reset chunks
        
        setIsProcessing(true);
        // Send to backend
        const formData = new FormData();
        // The backend expects an audio file
        formData.append("file", audioBlob, "recording.webm");

        try {
          const res = await fetch("http://localhost:8000/speech-to-text", {
            method: "POST",
            body: formData,
          });
          const data = await res.json();
          if (data.text) {
             onTranscriptionComplete(data.text);
          }
        } catch (err) {
          console.error("Speech to text error", err);
          alert("Error processing speech");
        } finally {
          setIsProcessing(false);
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Microphone access denied", err);
      alert("Microphone access is required to record voice.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      // Stop all audio tracks so the red recording blip goes away in the browser tab
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <button 
      onClick={toggleRecording} 
      className={`voice-btn ${isRecording ? 'recording' : ''}`}
      disabled={isProcessing}
      title={isRecording ? "Stop recording" : "Start recording"}
    >
      {isProcessing ? '⏳' : isRecording ? '⏹️' : '🎤'}
    </button>
  );
};

export default VoiceRecorder;
