'use client'

import { useState, useEffect } from 'react'
import styles from '@/styles/Chat.module.css'
import { type AIModel } from '@/types/ai'
import { Header } from './Header'
import { SidePanel } from './SidePanel'
import { sendChatRequest } from '@/utils/api'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export function Chat() {
  const [selectedModel, setSelectedModel] = useState<AIModel>('gpt3')
  const [selectedTopics, setSelectedTopics] = useState<string[]>([])
  const [sidePanelContent, setSidePanelContent] = useState<string>('')
  const [isSidePanelOpen, setIsSidePanelOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    const lastMessage = messages[messages.length - 1]
    if (lastMessage && lastMessage.role === 'assistant') {
      if (lastMessage.content.includes('```')) {
        setSidePanelContent(lastMessage.content)
        setIsSidePanelOpen(true)
      } else {
        setIsSidePanelOpen(false)
      }
    }
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMessage: Message = { id: Date.now().toString(), role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const data = await sendChatRequest([...messages, userMessage], selectedModel, selectedTopics)
      const assistantMessage: Message = { id: Date.now().toString(), role: 'assistant', content: data.response }
      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error:', error)
      // Обработка ошибки
    } finally {
      setIsLoading(false)
    }
  }

  const closeSidePanel = () => {
    setIsSidePanelOpen(false)
  }

  return (
    <div className={styles.container}>
      <Header 
        selectedModel={selectedModel}
        setSelectedModel={setSelectedModel}
        selectedTopics={selectedTopics}
        setSelectedTopics={setSelectedTopics}
      />
      <main className={styles.main}>
        <div className={styles.card}>
          <div className={styles.chatContainer}>
            <div className={styles.messageArea}>
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`${styles.message} ${
                    message.role === 'user' ? styles.userMessage : styles.assistantMessage
                  }`}
                >
                  <div
                    className={`${styles.messageContent} ${
                      message.role === 'user' ? styles.userMessageContent : styles.assistantMessageContent
                    }`}
                  >
                    {message.content.includes('```') 
                      ? 'Код отображен в боковой панели'
                      : message.content}
                  </div>
                </div>
              ))}
            </div>
            <form
              onSubmit={handleSubmit}
              className={styles.inputArea}
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me anything..."
                className={styles.input}
                disabled={isLoading}
              />
              <button type="submit" className={styles.sendButton} disabled={isLoading}>
                Send
              </button>
            </form>
          </div>
        </div>
        <SidePanel 
          content={sidePanelContent} 
          isOpen={isSidePanelOpen} 
          onClose={closeSidePanel} 
        />
      </main>
    </div>
  )
}

