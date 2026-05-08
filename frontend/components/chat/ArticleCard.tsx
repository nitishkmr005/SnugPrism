import { ExternalLink } from 'lucide-react'
import type { ArticleResult } from '@/lib/types'

export default function ArticleCard({ article }: { article: ArticleResult }) {
  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block border rounded-md p-2 text-xs hover:bg-muted transition-colors"
    >
      <div className="flex items-start gap-1">
        <ExternalLink className="h-3 w-3 mt-0.5 shrink-0 text-primary" />
        <div>
          <p className="font-medium text-foreground line-clamp-1">{article.title}</p>
          <p className="text-muted-foreground line-clamp-2 mt-0.5">{article.snippet}</p>
        </div>
      </div>
    </a>
  )
}
