'use client'
import type { ReactNode } from 'react'
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

function SidebarSection({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground/70 mb-1.5 px-1">
        {label}
      </p>
      {children}
    </div>
  )
}

function SidebarBtn({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full text-left px-3 py-1.5 rounded-lg text-sm transition-all ${
        active
          ? 'bg-primary text-primary-foreground font-semibold shadow-sm'
          : 'text-muted-foreground hover:text-foreground hover:bg-accent'
      }`}
    >
      {children}
    </button>
  )
}

export default function TopicSidebar({ topics, activeTopic, difficulty, sourceTag, onTopic, onDifficulty, onSourceTag }: Props) {
  return (
    <aside className="w-52 shrink-0 space-y-5 overflow-y-auto pb-4">
      <SidebarSection label="Topics">
        <ul className="space-y-0.5">
          <li>
            <SidebarBtn active={!activeTopic} onClick={() => onTopic('')}>
              All Topics
            </SidebarBtn>
          </li>
          {topics.map((t) => (
            <li key={t.slug}>
              <SidebarBtn active={activeTopic === t.slug} onClick={() => onTopic(t.slug)}>
                {t.label}
              </SidebarBtn>
            </li>
          ))}
        </ul>
      </SidebarSection>

      <div className="border-t border-border/50" />

      <SidebarSection label="Difficulty">
        <div className="space-y-0.5">
          <SidebarBtn active={!difficulty} onClick={() => onDifficulty('')}>All</SidebarBtn>
          {DIFFICULTY_OPTS.map((d) => (
            <SidebarBtn key={d} active={difficulty === d} onClick={() => onDifficulty(d)}>
              <span className="capitalize">{d}</span>
            </SidebarBtn>
          ))}
        </div>
      </SidebarSection>

      <div className="border-t border-border/50" />

      <SidebarSection label="Citation Source">
        <div className="space-y-0.5">
          <SidebarBtn active={!sourceTag} onClick={() => onSourceTag('')}>All Sources</SidebarBtn>
          {CITATION_SOURCES.map((s) => (
            <SidebarBtn key={s.tag} active={sourceTag === s.tag} onClick={() => onSourceTag(s.tag)}>
              {s.label}
            </SidebarBtn>
          ))}
        </div>
      </SidebarSection>
    </aside>
  )
}
