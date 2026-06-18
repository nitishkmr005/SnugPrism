'use client'
import { useState } from 'react'
import { ChevronDown, ChevronUp, ExternalLink, FileText } from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import DifficultyBadge from './DifficultyBadge'
import CodeBlock from './CodeBlock'
import ComparisonTable from './ComparisonTable'
import type { Question } from '@/lib/types'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function QuestionCard({ q, defaultOpen = false }: { q: Question; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader
        className="cursor-pointer select-none pb-3"
        onClick={() => setOpen((o) => !o)}
      >
        <div className="flex items-start justify-between gap-3">
          <p className="font-medium text-base leading-snug">{q.question}</p>
          <div className="flex items-center gap-2 shrink-0 mt-0.5">
            <DifficultyBadge difficulty={q.difficulty} />
            {open ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        </div>
        <div className="flex flex-wrap gap-1 mt-2">
          {q.tags.map((tag) => (
            <Badge key={tag} variant="secondary" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>
      </CardHeader>

      {open && (
        <CardContent className="pt-0">
          <Separator className="mb-4" />
          <div className="prose prose-sm max-w-none dark:prose-invert">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '')
                  if (match) {
                    return <CodeBlock code={String(children)} language={match[1]} />
                  }
                  return <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono" {...props}>{children}</code>
                },
                table({ children }) {
                  return (
                    <div className="overflow-x-auto">
                      <table className="border-collapse w-full text-sm">{children}</table>
                    </div>
                  )
                },
              }}
            >
              {q.answer}
            </ReactMarkdown>
          </div>

          {q.code_snippet && <CodeBlock code={q.code_snippet} />}
          {q.comparison_table && <ComparisonTable table={q.comparison_table} />}

          {(q.reference_urls.length > 0 || q.pdf_links.length > 0) && (
            <div className="mt-4 pt-3 border-t space-y-2">
              {q.reference_urls.map((url) => (
                <a
                  key={url}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-xs text-primary hover:underline"
                >
                  <ExternalLink className="h-3 w-3" />
                  {url.length > 70 ? url.slice(0, 67) + '…' : url}
                </a>
              ))}
              {q.pdf_links.map((link) => (
                <a
                  key={`${link.doc_id}-${link.page}`}
                  href={`${API}/api/documents/${link.doc_id}/pdf#page=${link.page}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 text-xs text-primary hover:underline"
                >
                  <FileText className="h-3 w-3" />
                  {link.label} (page {link.page})
                </a>
              ))}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  )
}
