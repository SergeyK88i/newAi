'use client'

import { useState } from 'react'
import styles from './Documentation.module.css'

interface Message {
  question: string
  answer: string
}

interface RelevantChunk {
  text: string
  score: number
}

export default function Documentation() {
  const [question, setQuestion] = useState('')
  const [history, setHistory] = useState<Message[]>([])
  const [relevantChunks, setRelevantChunks] = useState<RelevantChunk[]>([])

  const askQuestion = async () => {
    if (!question) return
    
    const response = await fetch('http://localhost:8000/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    })
    
    const data = await response.json()
    
    setHistory(prev => [...prev, { 
      question, 
      answer: data.answer 
    }])
    setRelevantChunks(data.relevant_chunks)
    setQuestion('')
  }

  const clearHistory = async () => {
    await fetch('http://localhost:8000/api/clear', {
      method: 'POST'
    })
    setHistory([])
    setRelevantChunks([])
  }

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Система консультации по документации</h1>
      
      {history.length > 0 && (
        <div className={styles.historySection}>
          <h2 className={styles.historyTitle}>История диалога:</h2>
          {history.map((msg, i) => (
            <div key={i} className={styles.messageCard}>
              <p><strong>Вопрос:</strong> {msg.question}</p>
              <p><strong>Ответ:</strong> {msg.answer}</p>
            </div>
          ))}
        </div>
      )}
      
      {relevantChunks.length > 0 && (
        <div className={styles.chunksSection}>
          <h2 className={styles.historyTitle}>Найденные релевантные фрагменты:</h2>
          {relevantChunks.map((chunk, i) => (
            <div key={i} className={styles.chunkCard}>
              <p>Релевантность: {chunk.score.toFixed(4)}</p>
              <p>Текст: {chunk.text}</p>
            </div>
          ))}
        </div>
      )}
      
      <div className={styles.inputSection}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Введите ваш вопрос"
          className={styles.input}
        />
        <button 
          onClick={askQuestion}
          className={`${styles.button} ${styles.askButton}`}
        >
          Спросить
        </button>
        <button 
          onClick={clearHistory}
          className={`${styles.button} ${styles.clearButton}`}
        >
          Очистить
        </button>
      </div>
    </div>
  )
}
