'use client'
import { Badge } from '@/components/ui/badge'
import type { Topic } from '@/lib/types'

const DIFFICULTY_OPTS = ['easy', 'medium', 'hard'] as const

interface Props {
  topics: Topic[]
  activeTopic: string
  difficulty: string
  onTopic: (s: string) => void
  onDifficulty: (s: string) => void
}

export default function TopicSidebar({ topics, activeTopic, difficulty, onTopic, onDifficulty }: Props) {
  return (
    <aside className="w-52 shrink-0 space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">Topics</p>
        <ul className="space-y-0.5">
          <li>
            <button
              onClick={() => onTopic('')}
              className={`w-full text-left px-3 py-1.5 rounded-md text-sm transition-colors ${
                !activeTopic ? 'bg-primary text-primary-foreground font-medium' : 'hover:bg-muted text-muted-foreground'
              }`}
            >
              All Topics
            </button>
          </li>
          {topics.map((t) => (
            <li key={t.slug}>
              <button
                onClick={() => onTopic(t.slug)}
                className={`w-full text-left px-3 py-1.5 rounded-md text-sm transition-colors ${
                  activeTopic === t.slug
                    ? 'bg-primary text-primary-foreground font-medium'
                    : 'hover:bg-muted text-muted-foreground'
                }`}
              >
                {t.label}
              </button>
            </li>
          ))}
        </ul>
      </div>

      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">Difficulty</p>
        <div className="flex flex-col gap-1">
          <button
            onClick={() => onDifficulty('')}
            className={`px-3 py-1.5 rounded-md text-sm text-left transition-colors ${
              !difficulty ? 'bg-primary text-primary-foreground font-medium' : 'hover:bg-muted text-muted-foreground'
            }`}
          >
            All
          </button>
          {DIFFICULTY_OPTS.map((d) => (
            <button
              key={d}
              onClick={() => onDifficulty(d)}
              className={`px-3 py-1.5 rounded-md text-sm text-left capitalize transition-colors ${
                difficulty === d ? 'bg-primary text-primary-foreground font-medium' : 'hover:bg-muted text-muted-foreground'
              }`}
            >
              {d}
            </button>
          ))}
        </div>
      </div>
    </aside>
  )
}
