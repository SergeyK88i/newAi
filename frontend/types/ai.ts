export type AIModel = 'gpt4' | 'gpt3'

export interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
}

