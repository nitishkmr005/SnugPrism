import { Badge } from '@/components/ui/badge'

const colors: Record<string, string> = {
  easy: 'bg-green-100 text-green-800 border-green-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  hard: 'bg-red-100 text-red-800 border-red-200',
}

export default function DifficultyBadge({ difficulty }: { difficulty: string }) {
  return (
    <Badge variant="outline" className={`text-xs font-medium ${colors[difficulty] || ''}`}>
      {difficulty}
    </Badge>
  )
}
