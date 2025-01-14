import { Checkbox } from "@/components/ui/checkbox"
import { topics } from "@/config/topics"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Settings } from 'lucide-react'

interface TopicSelectorProps {
  selectedTopics: string[]
  onTopicChange: (topics: string[]) => void
}

export function TopicSelector({ selectedTopics, onTopicChange }: TopicSelectorProps) {
  const toggleTopic = (topicId: string) => {
    const newTopics = selectedTopics.includes(topicId)
      ? selectedTopics.filter(id => id !== topicId)
      : [...selectedTopics, topicId]
    onTopicChange(newTopics)
  }

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="icon">
          <Settings className="h-4 w-4" />
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Select Topics</SheetTitle>
          <SheetDescription>
            Choose the topics you want the AI to focus on
          </SheetDescription>
        </SheetHeader>
        <div className="mt-4 space-y-4">
          {topics.map((topic) => (
            <div key={topic.id} className="flex items-start space-x-3">
              <Checkbox
                id={topic.id}
                checked={selectedTopics.includes(topic.id)}
                onCheckedChange={() => toggleTopic(topic.id)}
              />
              <div>
                <label
                  htmlFor={topic.id}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  {topic.label}
                </label>
                <p className="text-sm text-muted-foreground">
                  {topic.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </SheetContent>
    </Sheet>
  )
}

