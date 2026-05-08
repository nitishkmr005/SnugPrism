import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CodeBlock from '@/components/prep/CodeBlock'
import ArticleCard from './ArticleCard'
import type { ChatMessage as ChatMsg } from '@/lib/types'

export default function ChatMessage({ msg }: { msg: ChatMsg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted'
        }`}
      >
        {isUser ? (
          <p>{msg.content}</p>
        ) : (
          <>
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    if (match) return <CodeBlock code={String(children)} language={match[1]} />
                    return <code className="bg-background/50 px-1 py-0.5 rounded text-xs" {...props}>{children}</code>
                  },
                }}
              >
                {msg.content}
              </ReactMarkdown>
            </div>
            {msg.articles && msg.articles.length > 0 && (
              <div className="mt-2 space-y-1.5">
                <p className="text-xs text-muted-foreground font-medium">Related articles:</p>
                {msg.articles.map((a) => (
                  <ArticleCard key={a.url} article={a} />
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
