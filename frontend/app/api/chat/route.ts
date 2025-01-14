import { openai } from '@ai-sdk/openai'
import { streamText } from 'ai'
import { type AIModel } from '@/types/ai'
import { topics } from '@/config/topics'

export async function POST(req: Request) {
  const { messages, model, selectedTopics } = await req.json()
  
  const topicsContext = selectedTopics.length > 0
    ? `You are an AI assistant specialized in: ${selectedTopics
        .map(topicId => topics.find(t => t.id === topicId)?.label)
        .filter(Boolean)
        .join(', ')}. 
       Focus your responses on these topics and related best practices.`
    : 'You are a general AI assistant.'

  const systemMessage = `${topicsContext}
    When providing code examples or file contents, wrap them in triple backticks (\`\`\`).
    This will signal that the content should be displayed in a side panel.`

  const messagesWithContext = [
    { role: 'system', content: systemMessage },
    ...messages
  ]

  let aiModel
  switch (model) {
    case 'gpt4':
      aiModel = openai('gpt-4-turbo')
      break
    case 'gpt3':
      aiModel = openai('gpt-3.5-turbo')
      break
    default:
      aiModel = openai('gpt-3.5-turbo')
  }

  const result = streamText({
    model: aiModel,
    messages: messagesWithContext,
  })

  return result.toDataStreamResponse()
}

