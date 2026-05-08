'use client'
import { Badge } from '@/components/ui/badge'
import type { Topic } from '@/lib/types'

interface Props {
  topics: Topic[]
  selected: string[]
  onChange: (ids: string[]) => void
}

export default function TopicSelector({ topics, selected, onChange }: Props) {
  const toggle = (id: string) => {
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id])
  }
  return (
    <div>
      <p className="text-sm font-medium mb-1">Topics covered in this document</p>
      <p className="text-xs text-muted-foreground mb-2">Leave blank to auto-detect from content</p>
      <div className="flex flex-wrap gap-2">
        {topics.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => toggle(t.id)}
            className="focus:outline-none"
          >
            <Badge
              variant={selected.includes(t.id) ? 'default' : 'outline'}
              className="cursor-pointer hover:opacity-80 transition-opacity text-sm py-1 px-3"
            >
              {t.label}
            </Badge>
          </button>
        ))}
      </div>
    </div>
  )
}
