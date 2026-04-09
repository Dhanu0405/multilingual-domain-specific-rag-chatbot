import React, { useState, useRef } from 'react';

const AudioPlayer = ({ text, lang = "en", audioUrl }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef(null);

  const fetchAndPlay = async () => {
    // Phase 7: Instead of fetching /text-to-speech, directly stream from the returned audioUrl
    if (!audioRef.current && audioUrl) {
        audioRef.current = new Audio(audioUrl);
        audioRef.current.onended = () => setIsPlaying(false);
    }
    
    // Fallback if audioRef was correctly initialized
    if (audioRef.current) {
        if (isPlaying) {
            audioRef.current.pause();
            setIsPlaying(false);
        } else {
            audioRef.current.play();
            setIsPlaying(true);
        }
        return;
    }
  };

  return (
    <button 
      onClick={fetchAndPlay} 
      className="audio-btn" 
      disabled={!audioUrl}
      title="Listen to response"
    >
      {isPlaying ? "⏸️ Pause Audio" : "🔊 Listen"}
    </button>
  );
};

export default AudioPlayer;
