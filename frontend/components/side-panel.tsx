import React from 'react'
import { Card } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'

interface SidePanelProps {
  content: string
  isOpen: boolean
  onClose: () => void
}

export function SidePanel({ content, isOpen, onClose }: SidePanelProps) {
  if (!isOpen) return null

  return (
    <Card className="fixed right-0 top-0 h-full w-1/2 z-50 overflow-hidden">
      <div className="flex justify-between items-center p-4 border-b">
        <h2 className="text-lg font-semibold">Code Preview</h2>
        <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
          &times;
        </button>
      </div>
      <ScrollArea className="h-[calc(100vh-60px)] p-4">
        <pre className="whitespace-pre-wrap">{content}</pre>
      </ScrollArea>
    </Card>
  )
}

