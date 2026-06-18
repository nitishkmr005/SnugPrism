'use client'
import { useState } from 'react'
import TopicSidebar from '@/components/prep/TopicSidebar'
import SearchBar from '@/components/prep/SearchBar'
import QuestionCard from '@/components/prep/QuestionCard'
import { useTopics, useQuestions } from '@/lib/api'
import { ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'

const PAGE_SIZE = 10

export default function PrepPage() {
  const [topic, setTopic] = useState('')
  const [difficulty, setDifficulty] = useState('')
  const [sourceTag, setSourceTag] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)

  const { data: topics = [] } = useTopics()
  const { data, isLoading, error } = useQuestions({
    topic_slug: topic || undefined,
    difficulty: difficulty || undefined,
    tag: sourceTag || undefined,
    q: search || undefined,
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
  })

  const totalPages = data ? Math.max(1, Math.ceil(data.total / PAGE_SIZE)) : 1

  function handleFilterChange(setter: (v: string) => void) {
    return (v: string) => { setter(v); setPage(0) }
  }

  return (
    <div className="flex h-[calc(100vh-56px)] max-w-7xl mx-auto px-4 py-6 gap-8 overflow-hidden">
      <TopicSidebar
        topics={topics}
        activeTopic={topic}
        difficulty={difficulty}
        sourceTag={sourceTag}
        onTopic={handleFilterChange(setTopic)}
        onDifficulty={handleFilterChange(setDifficulty)}
        onSourceTag={handleFilterChange(setSourceTag)}
      />

      <div className="flex-1 min-w-0 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="mb-4 shrink-0">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h1 className="text-xl font-bold tracking-tight">
                {topic ? topics.find((t) => t.slug === topic)?.label : 'All Topics'}
              </h1>
              {sourceTag && (
                <p className="text-xs text-primary font-medium mt-0.5">
                  Filtered by: {sourceTag.replace('source:', '')}
                </p>
              )}
            </div>
            {data && (
              <span className="inline-flex items-center rounded-full bg-primary/8 px-2.5 py-1 text-xs font-semibold text-primary">
                {data.total} questions
              </span>
            )}
          </div>
          <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(0) }} />
        </div>

        {/* Question list — scrolls within the fixed height */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-3">
          {isLoading && (
            <div className="flex justify-center py-20">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}
          {error && (
            <p className="text-center text-destructive py-10">
              Failed to load questions. Is the backend running?
            </p>
          )}
          {!isLoading && data && data.items.length === 0 && (
            <p className="text-center text-muted-foreground py-10">No questions found.</p>
          )}
          {data?.items.map((q, idx) => (
            <QuestionCard key={q.id} q={q} defaultOpen={idx === 0 && page === 0} />
          ))}
        </div>

        {/* Pagination — pinned to bottom */}
        {data && data.total > PAGE_SIZE && (
          <div className="flex items-center justify-between pt-4 border-t shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p - 1)}
              disabled={page === 0}
            >
              <ChevronLeft className="h-4 w-4 mr-1" />
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {page + 1} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= totalPages - 1}
            >
              Next
              <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
