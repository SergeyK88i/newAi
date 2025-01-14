'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Send } from 'lucide-react'
import { type AIModel } from '@/types/ai'
import { Header } from './header'
import { SidePanel } from './side-panel'
import { sendChatRequest } from '@/utils/api'

// Определим интерфейс для сообщений
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
      if (lastMessage.content.includes('\`\`\`')) {
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
    <div className="flex flex-col min-h-screen">
      <Header 
        selectedModel={selectedModel}
        setSelectedModel={setSelectedModel}
        selectedTopics={selectedTopics}
        setSelectedTopics={setSelectedTopics}
      />
      <main className="flex-1 py-8 relative">
        <Card className="max-w-3xl mx-auto">
          <div className="flex flex-col h-[600px]">
            <ScrollArea className="flex-1 p-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`mb-4 flex ${
                    message.role === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`rounded-lg px-4 py-2 max-w-[80%] ${
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted'
                    }`}
                  >
                    {message.content.includes('\`\`\`') 
                      ? 'Код отображен в боковой панели'
                      : message.content}
                  </div>
                </div>
              ))}
            </ScrollArea>
            <form
              onSubmit={handleSubmit}
              className="border-t p-4 flex items-center gap-4"
            >
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask me anything..."
                className="flex-1"
                disabled={isLoading}
              />
              <Button type="submit" size="icon" disabled={isLoading}>
                <Send className="h-4 w-4" />
                <span className="sr-only">Send</span>
              </Button>
            </form>
          </div>
        </Card>
        <SidePanel 
          content={sidePanelContent} 
          isOpen={isSidePanelOpen} 
          onClose={closeSidePanel} 
        />
      </main>
    </div>
  )
}

