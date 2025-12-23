import React, { useState, useRef, useEffect } from 'react';
import styles from './ChatWidget.module.css';

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedText, setSelectedText] = useState('');
  const messagesEndRef = useRef(null);

  // Initialize user profile on mount fix deposit
  useEffect(() => {
    // Check if user profile exists in localStorage
    const userProfile = localStorage.getItem('userProfile');
    if (!userProfile) {
      // Set a default profile for demo purposes
      // In production, this would be set during login from better-auth
      const defaultProfile = {
        experienceLevel: 'beginner',
        softwareBackground: 'Basic Python',
        hardwareBackground: 'None'
      };
      localStorage.setItem('userProfile', JSON.stringify(defaultProfile));
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Detect text selection
  useEffect(() => {
    const handleSelection = () => {
      const selection = window.getSelection();
      const text = selection.toString().trim();
      if (text && text.length > 10) {
        setSelectedText(text);
      }
    };

    document.addEventListener('mouseup', handleSelection);
    return () => document.removeEventListener('mouseup', handleSelection);
  }, []);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input,
          selected_text: selectedText || null
        })
      });

      const data = await response.json();
      
      const botMessage = { 
        role: 'assistant', 
        content: data.response,
        sources: data.sources || []
      };
      
      setMessages(prev => [...prev, botMessage]);
      setSelectedText(''); // Clear selected text after use
    } catch (error) {
      const errorMessage = { 
        role: 'assistant', 
        content: '❌ Error: Could not connect to chatbot. Make sure the backend is running on http://localhost:8000'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {/* Floating Chat Button */}
      <button 
        className={styles.chatButton}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle chat"
      >
        {isOpen ? '✕' : '💬'}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className={styles.chatWindow}>
          <div className={styles.chatHeader}>
            <h3>🤖 Physical AI Assistant</h3>
            {selectedText && (
              <div className={styles.selectedTextBadge}>
                📝 Text selected
              </div>
            )}
          </div>

          <div className={styles.chatMessages}>
            {messages.length === 0 && (
              <div className={styles.welcomeMessage}>
                <p>👋 Hi! I'm your Physical AI & Humanoid Robotics assistant.</p>
                <p>Ask me anything about the textbook!</p>
                <p><strong>Tip:</strong> Select text on the page and ask questions about it!</p>
              </div>
            )}
            
            {messages.map((msg, idx) => (
              <div 
                key={idx} 
                className={msg.role === 'user' ? styles.userMessage : styles.botMessage}
              >
                <div className={styles.messageContent}>
                  {msg.content}
                </div>
                
                {msg.sources && msg.sources.length > 0 && (
                  <div className={styles.sources}>
                    <strong>Sources:</strong>
                    {msg.sources.map((source, i) => (
                      <div key={i} className={styles.source}>
                        📄 {source.source}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
            
            {loading && (
              <div className={styles.botMessage}>
                <div className={styles.typing}>
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          <div className={styles.chatInput}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question..."
              rows="2"
            />
            <button 
              onClick={sendMessage}
              disabled={loading || !input.trim()}
            >
              {loading ? '⏳' : '➤'}
            </button>
          </div>
        </div>
      )}
    </>
  );
}