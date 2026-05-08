'use client'
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react'
import { useIngestStatus } from '@/lib/api'

export default function IngestStatus({ docId }: { docId: string }) {
  const { data } = useIngestStatus(docId)
  if (!data) return null

  if (data.status === 'processing') {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Processing document… this may take a minute.
      </div>
    )
  }
  if (data.status === 'done') {
    return (
      <div className="flex items-center gap-2 text-sm text-green-700">
        <CheckCircle2 className="h-4 w-4" />
        Done! {data.chunk_count} chunks · {data.qa_count} Q&amp;As generated
      </div>
    )
  }
  return (
    <div className="flex items-center gap-2 text-sm text-red-600">
      <XCircle className="h-4 w-4" />
      Failed: {data.error || 'Unknown error'}
    </div>
  )
}
