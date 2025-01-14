'use client'

import { useState, useRef } from 'react'
import styles from './Documentation.module.css'

interface Message {
  type: 'user' | 'bot'
  content: string
  chunks?: Array<{ text: string; score: number }>
}

export default function Documentation() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [showSidebar, setShowSidebar] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
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
  
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <button 
          className={styles.menuButton}
          onClick={() => setShowSidebar(!showSidebar)}
        >
          ☰
        </button>
        <h1 className={styles.title}>Документация</h1>
      </div>

      <div className={styles.mainContent}>
        <aside className={`${styles.sidebar} ${showSidebar ? styles.sidebarOpen : ''}`}>
          <h2>История запросов</h2>
          <div className={styles.historyList}>
            {messages
              .filter(m => m.type === 'user')
              .map((m, i) => (
                <div key={i} className={styles.historyItem}>
                  {m.content}
                </div>
            ))}
          </div>
        </aside>

        <main className={styles.chatArea}>
          <div className={styles.messages}>
            {messages.map((message, i) => (
              <div key={i} className={`${styles.message} ${styles[message.type]}`}>
                {message.content}
              </div>
            ))}
          </div>

          <form onSubmit={handleSubmit} className={styles.inputForm}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Задайте вопрос..."
              className={styles.input}
            />
            <button type="submit" className={styles.sendButton}>
              →
            </button>
          </form>
        </main>
      </div>
    </div>
  )
}
