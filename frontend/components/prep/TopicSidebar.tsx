'use client'
import type { Topic } from '@/lib/types'

const DIFFICULTY_OPTS = ['easy', 'medium', 'hard'] as const

const CITATION_SOURCES = [
  { label: 'SBERT / SentenceTransformers', tag: 'source:sbert' },
  { label: 'HuggingFace / MTEB', tag: 'source:huggingface' },
  { label: 'OpenAI', tag: 'source:openai' },
  { label: 'Cohere', tag: 'source:cohere' },
  { label: 'Voyage AI', tag: 'source:voyageai' },
  { label: 'RAGAS', tag: 'source:ragas' },
  { label: 'Pinecone', tag: 'source:pinecone' },
  { label: 'Qdrant', tag: 'source:qdrant' },
] as const

interface Props {
  topics: Topic[]
  activeTopic: string
  difficulty: string
  sourceTag: string
  onTopic: (s: string) => void
  onDifficulty: (s: string) => void
  onSourceTag: (s: string) => void
}

export default function TopicSidebar({ topics, activeTopic, difficulty, sourceTag, onTopic, onDifficulty, onSourceTag }: Props) {
  return (
    <aside className="w-52 shrink-0 space-y-6 overflow-y-auto">
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

      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">Citation Source</p>
        <div className="flex flex-col gap-1">
          <button
            onClick={() => onSourceTag('')}
            className={`px-3 py-1.5 rounded-md text-sm text-left transition-colors ${
              !sourceTag ? 'bg-primary text-primary-foreground font-medium' : 'hover:bg-muted text-muted-foreground'
            }`}
          >
            All Sources
          </button>
          {CITATION_SOURCES.map((s) => (
            <button
              key={s.tag}
              onClick={() => onSourceTag(s.tag)}
              className={`px-3 py-1.5 rounded-md text-sm text-left transition-colors ${
                sourceTag === s.tag ? 'bg-primary text-primary-foreground font-medium' : 'hover:bg-muted text-muted-foreground'
              }`}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>
    </aside>
  )
}
