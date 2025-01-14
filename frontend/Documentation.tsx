'use client'

import { useState, useRef, useEffect } from 'react'
import styles from './Documentation.module.css'

interface Message {
  type: 'user' | 'bot'
  content: string
  chunks?: Array<{ text: string; score: number }>
}

export default function Documentation() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!input.trim()) return

    const userMessage = input
    setInput('')
    setMessages(prev => [...prev, { type: 'user', content: userMessage }])

    const response = await fetch('http://localhost:8000/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: userMessage })
    })
    
    const data = await response.json()
    
    setMessages(prev => [...prev, { 
      type: 'bot', 
      content: data.answer,
      chunks: data.relevant_chunks 
    }])
  }

  const clearHistory = async () => {
    await fetch('http://localhost:8000/api/clear', { method: 'POST' })
    setMessages([])
  }

  return (
    <div className={styles.container}>
      <div className={styles.chatContainer}>
        <button 
          onClick={clearHistory}
          className={styles.clearButton}
        >
          Очистить историю
        </button>
        
        <div className={styles.messagesContainer}>
          {messages.map((message, i) => (
            <div 
              key={i} 
              className={`${styles.message} ${
                message.type === 'user' ? styles.userMessage : ''
              }`}
            >
              <div className={`${styles.messageContent} ${
                message.type === 'user' ? styles.userMessageContent : styles.botMessageContent
              }`}>
                {message.content}
                {message.chunks && (
                  <div className={styles.relevantChunks}>
                    {message.chunks.map((chunk, j) => (
                      <div key={j}>
                        <small>Релевантность: {chunk.score.toFixed(4)}</small>
                        <p>{chunk.text}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <form 
          className={styles.inputContainer} 
          onSubmit={handleSubmit}
        >
          <div className={styles.inputWrapper}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Задайте вопрос..."
              className={styles.input}
            />
            <button 
              type="submit"
              className={styles.sendButton}
              disabled={!input.trim()}
            >
              →
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
