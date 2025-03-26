
import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, StopCircle } from 'lucide-react';
import { toast } from 'sonner';

interface VoiceInputProps {
  onTranscript: (transcript: string) => void;
  disabled?: boolean;
}

const VoiceInput: React.FC<VoiceInputProps> = ({ onTranscript, disabled = false }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    // Check if browser supports SpeechRecognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setIsSupported(false);
      return;
    }

    // Initialize SpeechRecognition
    recognitionRef.current = new SpeechRecognition();
    recognitionRef.current.continuous = true;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = 'en-US';

    recognitionRef.current.onresult = (event: any) => {
      const transcript = Array.from(event.results)
        .map((result: any) => result[0])
        .map((result: any) => result.transcript)
        .join('');
      
      // Only use the final result when recording stops
      if (event.results[0].isFinal) {
        onTranscript(transcript);
      }
    };

    recognitionRef.current.onerror = (event: any) => {
      console.error('Speech recognition error', event.error);
      toast.error('Error with speech recognition. Please try again.');
      stopRecording();
    };

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, [onTranscript]);

  const startRecording = async () => {
    if (disabled) return;
    
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      setIsRecording(true);
      recognitionRef.current.start();
      toast.info('Listening... Speak now');
    } catch (error) {
      console.error('Error accessing microphone:', error);
      toast.error('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsRecording(false);
  };

  if (!isSupported) {
    return (
      <button
        type="button"
        className="text-gray-400 cursor-not-allowed"
        disabled={true}
        title="Voice input not supported in this browser"
      >
        <MicOff size={18} />
      </button>
    );
  }

  return (
    <button
      type="button"
      className={`p-2 rounded-full ${
        isRecording 
          ? 'bg-red-500 text-white animate-pulse' 
          : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
      }`}
      onClick={isRecording ? stopRecording : startRecording}
      disabled={disabled}
      aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
      title={isRecording ? 'Stop recording' : 'Start voice input'}
    >
      {isRecording ? <StopCircle size={18} /> : <Mic size={18} />}
    </button>
  );
};

export default VoiceInput;
