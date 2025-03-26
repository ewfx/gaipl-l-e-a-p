
import React, { useState, useRef, useEffect } from 'react';
import ChatMessage, { Message } from './ChatMessage';
import ChatInput from './ChatInput';
import { generateResponse, createMessage } from '@/lib/chatbot';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { toast } from 'sonner';
import BackendStatus from './BackendStatus';

interface ChatBotProps {
  initialMessage?: string;
}

const ChatBot: React.FC<ChatBotProps> = ({ initialMessage = "Hello! I'm OpsBuddy, your intelligent incident resolution assistant. How can I help you today?" }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [apiKey, setApiKey] = useState<string>('');
  const [isApiKeyDialogOpen, setIsApiKeyDialogOpen] = useState<boolean>(false);

  useEffect(() => {
    // Add the initial bot message when component mounts
    const botMessage = createMessage(initialMessage, 'bot', 'info');
    setMessages([botMessage]);
  }, [initialMessage]);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (content: string) => {
    const userMessage = createMessage(content, 'user');
    
    setMessages(prev => [...prev, userMessage]);
    
    // Check if the user is asking to configure OpenAI
    if (content.toLowerCase().includes('api key') || content.toLowerCase().includes('openai')) {
      if (!content.includes('sk-')) {
        setIsApiKeyDialogOpen(true);
        return;
      }
    }
    
    try {
      await generateResponse(
        content,
        () => setIsTyping(true),
        (response, severity) => {
          setIsTyping(false);
          const botMessage = createMessage(response, 'bot', severity);
          setMessages(prev => [...prev, botMessage]);
        }
      );
    } catch (error) {
      console.error('Error in handleSendMessage:', error);
      setIsTyping(false);
      toast.error('Failed to generate a response. Please try again.');
    }
  };

  const handleApiKeySubmit = () => {
    if (!apiKey.trim() || !apiKey.startsWith('sk-') || apiKey.length < 20) {
      toast.error('Please enter a valid OpenAI API key');
      return;
    }
    
    // Send the API key as a message (will be processed by the generateResponse function)
    handleSendMessage(`Setting up my API key: ${apiKey}`);
    setIsApiKeyDialogOpen(false);
    setApiKey('');
  };

  return (
    <div className="chatbot-container h-[600px] md:h-[70vh]">
      <div className="flex justify-end mb-2">
        <BackendStatus />
      </div>
      
      <div className="chatbot-messages flex-1 overflow-y-auto" style={{ scrollBehavior: 'smooth' }}>
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        
        {isTyping && (
          <div className="message-bot opacity-80">
            <div className="typing-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      <ChatInput onSendMessage={handleSendMessage} disabled={isTyping} />
      
      <Dialog open={isApiKeyDialogOpen} onOpenChange={setIsApiKeyDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Enter your OpenAI API Key</DialogTitle>
            <DialogDescription>
              The API key is needed to enable AI-powered analysis. It will be stored only in your browser session and never sent to our servers.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Input
              type="password"
              placeholder="sk-..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsApiKeyDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleApiKeySubmit}>Submit</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ChatBot;
