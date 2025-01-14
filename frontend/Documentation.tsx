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
  
  return (
    <div className={styles.container}>
      {/* Верхняя панель */}
      <header className={styles.header}>
        <button onClick={() => setShowSidebar(!showSidebar)}>
          ☰ История
        </button>
        <h1>Документация</h1>
      </header>

      {/* Основной контент */}
      <div className={styles.content}>
        {/* Выдвижная панель */}
        {showSidebar && (
          <aside className={styles.sidebar}>
            <h2>История запросов</h2>
            {messages.filter(m => m.type === 'user').map((m, i) => (
              <div key={i} className={styles.historyItem}>
                {m.content}
              </div>
            ))}
          </aside>
        )}

        {/* Чат */}
        <main className={styles.chat}>
          <div className={styles.messages}>
            {messages.map((message, i) => (
              <div key={i} className={styles.messageWrapper}>
                <div className={`${styles.message} ${styles[message.type]}`}>
                  <div className={styles.messageContent}>
                    {message.content}
                  </div>
                  {message.chunks && (
                    <div className={styles.chunks}>
                      <button className={styles.showChunks}>
                        Показать релевантные фрагменты
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className={styles.inputWrapper}>
            <input
              className={styles.input}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Задайте вопрос..."
            />
          </div>
        </main>
      </div>
    </div>
  )
}
