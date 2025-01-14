import Link from 'next/link'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Button } from '@/components/ui/button'
import { TopicSelector } from './topic-selector'
import { type AIModel } from '@/types/ai'

interface HeaderProps {
  selectedModel: AIModel
  setSelectedModel: (model: AIModel) => void
  selectedTopics: string[]
  setSelectedTopics: (topics: string[]) => void
}

export function Header({ selectedModel, setSelectedModel, selectedTopics, setSelectedTopics }: HeaderProps) {
  return (
    <header className="border-b">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <Link href="/" className="font-bold text-2xl">
          AI Chat
        </Link>
        <div className="flex items-center gap-4">
          <Select
            value={selectedModel}
            onValueChange={(value) => setSelectedModel(value as AIModel)}
          >
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Select AI Model" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="gpt4">GPT-4 Turbo</SelectItem>
              <SelectItem value="gpt3">GPT-3.5 Turbo</SelectItem>
            </SelectContent>
          </Select>
          <TopicSelector 
            selectedTopics={selectedTopics}
            onTopicChange={setSelectedTopics}
          />
        </div>
      </div>
    </header>
  )
}

