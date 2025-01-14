import { useState, useEffect } from 'react'
import { topics } from '@/config/topics'
import styles from '@/styles/TopicSelector.module.css'

interface TopicSelectorProps {
  selectedTopics: string[]
  onTopicChange: (topics: string[]) => void
}

export function TopicSelector({ selectedTopics, onTopicChange }: TopicSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)

  const toggleSidebar = () => setIsOpen(!isOpen)

  const toggleTopic = (topicId: string) => {
    const newTopics = selectedTopics.includes(topicId)
      ? selectedTopics.filter(id => id !== topicId)
      : [...selectedTopics, topicId]
    onTopicChange(newTopics)
  }

  useEffect(() => {
    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }
    window.addEventListener('keydown', handleEsc)

    return () => {
      window.removeEventListener('keydown', handleEsc)
    }
  }, [])

  return (
    <div className={styles.topicSelector}>
      <button onClick={toggleSidebar} className={styles.toggleButton}>
        ☰
      </button>
      <div className={`${styles.sidebar} ${isOpen ? styles.sidebarOpen : ''}`}>
        <div className={styles.sidebarHeader}>
          <h2>Select Topics</h2>
          <button onClick={toggleSidebar} className={styles.closeButton}>
            &times;
          </button>
        </div>
        <div className={styles.topicList}>
          {topics.map((topic) => (
            <div key={topic.id} className={styles.topicItem}>
              <input
                type="checkbox"
                id={topic.id}
                checked={selectedTopics.includes(topic.id)}
                onChange={() => toggleTopic(topic.id)}
              />
              <label htmlFor={topic.id}>{topic.label}</label>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

