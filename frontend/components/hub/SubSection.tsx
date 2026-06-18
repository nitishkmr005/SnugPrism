'use client'
import { useState } from 'react'
import { ChevronDown, ChevronUp, BookOpen } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CodeBlock from '@/components/prep/CodeBlock'
import DiagramBlock from './DiagramBlock'
import type { HubSection } from '@/lib/types'

export default function SubSection({ section, defaultOpen = false }: { section: HubSection; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className="mb-2 rounded-xl border bg-card overflow-hidden transition-all hover:shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between gap-3 px-5 py-4 text-left group"
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="flex items-center justify-center h-7 w-7 rounded-lg bg-primary/10 shrink-0">
            <BookOpen className="h-3.5 w-3.5 text-primary" />
          </span>
          <span className="font-semibold text-sm sm:text-base leading-snug group-hover:text-primary transition-colors">
            {section.title}
          </span>
        </div>
        <span className="shrink-0 text-muted-foreground group-hover:text-foreground transition-colors">
          {open
            ? <ChevronUp className="h-4 w-4" />
            : <ChevronDown className="h-4 w-4" />
          }
        </span>
      </button>

      {open && (
        <div className="border-t px-5 pb-7 pt-5">
          {section.diagram_def && (
            <div className="mb-5">
              <DiagramBlock definition={section.diagram_def} />
            </div>
          )}
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '')
                  if (match) return <CodeBlock code={String(children)} language={match[1]} />
                  return (
                    <code
                      className="bg-muted px-1.5 py-0.5 rounded text-[0.82em] font-mono"
                      {...props}
                    >
                      {children}
                    </code>
                  )
                },
              }}
            >
              {section.content}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  )
}
