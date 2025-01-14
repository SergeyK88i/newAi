import React from 'react'
import styles from '@/styles/Layout.module.css'

interface LayoutProps {
  children: React.ReactNode
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className={styles.container}>
      {children}
    </div>
  )
}

