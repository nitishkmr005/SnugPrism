import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CodeBlock from '@/components/prep/CodeBlock'
import DiagramBlock from './DiagramBlock'
import type { HubSection } from '@/lib/types'

export default function SubSection({ section }: { section: HubSection }) {
  return (
    <div className="mb-8">
      <h3 className="text-lg font-semibold mb-3">{section.title}</h3>
      {section.diagram_def && <DiagramBlock definition={section.diagram_def} />}
      <div className="prose prose-sm max-w-none dark:prose-invert">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ node, className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '')
              if (match) return <CodeBlock code={String(children)} language={match[1]} />
              return <code className="bg-muted px-1 py-0.5 rounded text-sm" {...props}>{children}</code>
            },
          }}
        >
          {section.content}
        </ReactMarkdown>
      </div>
    </div>
  )
}
