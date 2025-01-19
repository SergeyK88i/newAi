import { Message } from '@/types/ai'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function sendChatRequest(messages: Message[], model: string, selectedTopics: string[]) {
  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages,
      model,
      selectedTopics,
    }),
  })

  if (!response.ok) {
    throw new Error('Failed to get response from server')
  }

  return response.json()
}

