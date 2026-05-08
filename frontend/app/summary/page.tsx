'use client'
import { useRunSummary } from '@/lib/api'
import RunSummaryTable from '@/components/summary/RunSummaryTable'
import { Loader2, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function SummaryPage() {
  const { data, isLoading, error, refetch, isFetching } = useRunSummary()

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Run Summary</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Token usage and cost for every LLM and embedding call. Auto-refreshes every 30s.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
          <RefreshCw className={`h-4 w-4 mr-1.5 ${isFetching ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {isLoading && (
        <div className="flex justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {error && (
        <p className="text-center text-destructive py-10">
          Failed to load run summary. Is the backend running?
        </p>
      )}

      {data && data.total_calls === 0 && (
        <p className="text-center text-muted-foreground py-10">
          No API calls logged yet. Use the chat or ingest a document to start tracking.
        </p>
      )}

      {data && data.total_calls > 0 && <RunSummaryTable data={data} />}
    </div>
  )
}
