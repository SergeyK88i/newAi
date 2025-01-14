import styles from '@/styles/SidePanel.module.css'

interface SidePanelProps {
  content: string
  isOpen: boolean
  onClose: () => void
}

export function SidePanel({ content, isOpen, onClose }: SidePanelProps) {
  if (!isOpen) return null

  return (
    <div className={styles.sidePanel}>
      <div className={styles.header}>
        <h2 className={styles.title}>Code Preview</h2>
        <button onClick={onClose} className={styles.closeButton}>
          &times;
        </button>
      </div>
      <div className={styles.content}>
        <pre className={styles.codeBlock}>{content}</pre>
      </div>
    </div>
  )
}

