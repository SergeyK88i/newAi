import Link from 'next/link'
import styles from '@/styles/Header.module.css'
import { AIModel } from '@/types/ai'
import { TopicSelector } from './TopicSelector'

interface HeaderProps {
  selectedModel: AIModel
  setSelectedModel: (model: AIModel) => void
  selectedTopics: string[]
  setSelectedTopics: (topics: string[]) => void
}

export function Header({ selectedModel, setSelectedModel, selectedTopics, setSelectedTopics }: HeaderProps) {
  return (
    <header className={styles.header}>
      <div className={styles.headerContent}>
        <Link href="/" className={styles.logo}>
          AI Chat
        </Link>
        <div className={styles.controls}>
          <select 
            value={selectedModel} 
            onChange={(e) => setSelectedModel(e.target.value as AIModel)}
            className={styles.modelSelect}
          >
            <option value="gpt4">GPT-4 Turbo</option>
            <option value="gpt3">GPT-3.5 Turbo</option>
          </select>
          <TopicSelector 
            selectedTopics={selectedTopics}
            onTopicChange={setSelectedTopics}
          />
        </div>
      </div>
    </header>
  )
}

