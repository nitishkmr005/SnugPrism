'use client'
import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import SubSection from '@/components/hub/SubSection'
import { useTopics, useHub } from '@/lib/api'
import { ExternalLink, FileText, Globe, Loader2, MessageSquare } from 'lucide-react'
import type { Document } from '@/lib/types'

function DocumentCard({ doc }: { doc: Document }) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border bg-card text-card-foreground">
      {doc.source_type === 'url'
        ? <Globe className="h-4 w-4 text-muted-foreground shrink-0" />
        : <FileText className="h-4 w-4 text-muted-foreground shrink-0" />}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{doc.title}</p>
        <p className="text-xs text-muted-foreground">{doc.chunk_count} chunks indexed</p>
      </div>
      {doc.source_type === 'url' && (
        <a href={doc.source_ref} target="_blank" rel="noopener noreferrer" className="shrink-0">
          <ExternalLink className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground transition-colors" />
        </a>
      )}
    </div>
  )
}

function HubTopicContent({ slug }: { slug: string }) {
  const { data, isLoading, error } = useHub(slug)
  if (isLoading) return <div className="py-12 flex justify-center"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
  if (error || !data) return <p className="text-muted-foreground py-8 text-center">Content not yet available for this topic.</p>

  return (
    <div>
      {data.sections.length === 0 && data.documents.length === 0 && (
        <p className="text-muted-foreground py-8 text-center">No content yet. Run the seed script or ingest a document.</p>
      )}

      {data.sections.map((section) => (
        <SubSection key={section.id} section={section} />
      ))}

      {data.documents.length > 0 && (
        <div className="mt-8">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
              Ingested Sources · {data.documents.length}
            </h3>
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <MessageSquare className="h-3 w-3" />
              Ask the chat widget below to search these
            </span>
          </div>
          <div className="space-y-2">
            {data.documents.map((doc) => (
              <DocumentCard key={doc.id} doc={doc} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default function HubPage() {
  const { data: topics = [], isLoading } = useTopics()
  const [activeTab, setActiveTab] = useState<string>('')

  if (isLoading) return <div className="flex justify-center py-20"><Loader2 className="h-8 w-8 animate-spin text-muted-foreground" /></div>
  if (!topics.length) return null

  const active = activeTab || topics[0]?.slug || ''

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Learning Hub</h1>
        <p className="text-muted-foreground text-sm mt-1">Structured deep dives · ingested documents · RAG-powered chat</p>
      </div>
      <Tabs value={active} onValueChange={setActiveTab}>
        <TabsList className="flex flex-wrap h-auto gap-1 mb-6">
          {topics.map((t) => (
            <TabsTrigger key={t.slug} value={t.slug} className="text-xs sm:text-sm">
              {t.label}
            </TabsTrigger>
          ))}
        </TabsList>
        {topics.map((t) => (
          <TabsContent key={t.slug} value={t.slug}>
            <HubTopicContent slug={t.slug} />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
