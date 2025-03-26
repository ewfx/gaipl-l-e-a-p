
import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import VoiceInput from './VoiceInput';
import { toast } from 'sonner';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled = false }) => {
  const [message, setMessage] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus();
    }
  }, [disabled]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      try {
        // Make API call to the backend
        const response = await fetch('http://localhost:5000/query', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query: message }),
        });
        
        if (!response.ok) {
          throw new Error('Failed to get response from server');
        }
        
        const data = await response.json();
        console.log('Backend response:', data);
      } catch (error) {
        console.error('Error calling backend API:', error);
        toast.error('Failed to connect to backend. Using fallback mode.', {
          duration: 3000,
          position: 'bottom-right',
        });
      }
      
      // Pass the message to the parent component
      onSendMessage(message);
      
      // Clear the input
      setMessage('');
      
      // Reset the height of the textarea
      if (inputRef.current) {
        inputRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);

    // Auto-resize the textarea
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 150)}px`;
    }
  };

  const handleVoiceTranscript = (transcript: string) => {
    setMessage(transcript);
    
    // Wait for state update and then resize the textarea
    setTimeout(() => {
      if (inputRef.current) {
        inputRef.current.style.height = 'auto';
        inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 150)}px`;
      }
    }, 0);
  };

  return (
    <form onSubmit={handleSubmit} className="chatbot-input-container">
      <div className="relative flex items-center">
        <VoiceInput onTranscript={handleVoiceTranscript} disabled={disabled} />
        <textarea
          ref={inputRef}
          className="chatbot-input pl-12"
          placeholder="Type a message or click the mic to speak..."
          value={message}
          onChange={handleTextareaChange}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          rows={1}
          style={{ minHeight: '44px', maxHeight: '150px' }}
        />
        <button
          type="submit"
          className="chatbot-send-button"
          disabled={!message.trim() || disabled}
          aria-label="Send message"
        >
          <Send size={18} />
        </button>
      </div>
    </form>
  );
};

export default ChatInput;
