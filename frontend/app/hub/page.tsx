'use client'
import { useState } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import SubSection from '@/components/hub/SubSection'
import { postJson, useTopics, useHub } from '@/lib/api'
import { ExternalLink, Eye, FileText, Globe, Loader2, MessageSquare, Sparkles, X } from 'lucide-react'
import type { Document } from '@/lib/types'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function pdfUrl(docId: string) {
  return `${API}/api/documents/${docId}/pdf`
}

function DocumentCard({
  doc,
  onPreviewPdf,
  onRegenerate,
  regenerating,
}: {
  doc: Document
  onPreviewPdf: (doc: Document) => void
  onRegenerate: (doc: Document) => void
  regenerating: boolean
}) {
  const href = doc.source_type === 'url'
    ? doc.source_ref
    : pdfUrl(doc.id)

  const content = (
    <>
      {doc.source_type === 'url'
        ? <Globe className="h-4 w-4 text-muted-foreground shrink-0" />
        : <FileText className="h-4 w-4 text-muted-foreground shrink-0" />}
      <div className="flex-1 min-w-0 text-left">
        <p className="text-sm font-medium truncate">{doc.title}</p>
        <p className="text-xs text-muted-foreground">{doc.chunk_count} chunks indexed</p>
      </div>
      {doc.source_type === 'url'
        ? <ExternalLink className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
        : <Eye className="h-3.5 w-3.5 text-muted-foreground shrink-0" />}
    </>
  )

  return (
    <div className="flex items-stretch gap-2 rounded-lg border bg-card text-card-foreground p-1">
      {doc.source_type === 'pdf' ? (
      <button
        type="button"
        onClick={() => onPreviewPdf(doc)}
        className="flex min-w-0 flex-1 items-center gap-3 rounded-md p-2 hover:bg-accent transition-colors"
      >
        {content}
      </button>
      ) : (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="flex min-w-0 flex-1 items-center gap-3 rounded-md p-2 hover:bg-accent transition-colors"
        >
          {content}
        </a>
      )}
      <button
        type="button"
        onClick={() => onRegenerate(doc)}
        disabled={regenerating}
        className="inline-flex w-9 items-center justify-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground disabled:opacity-50"
        aria-label="Regenerate Q&A"
        title="Regenerate Q&A"
      >
        {regenerating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
      </button>
    </div>
  )
}

function PdfPreview({ doc, onClose }: { doc: Document; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 bg-background">
      <div className="flex h-12 items-center justify-between border-b px-4">
        <div className="flex min-w-0 items-center gap-2">
          <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
          <p className="truncate text-sm font-medium">{doc.title}</p>
        </div>
        <div className="flex items-center gap-1">
          <a
            href={pdfUrl(doc.id)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex h-8 w-8 items-center justify-center rounded-md hover:bg-accent"
            aria-label="Open PDF in new tab"
          >
            <ExternalLink className="h-4 w-4" />
          </a>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-8 w-8 items-center justify-center rounded-md hover:bg-accent"
            aria-label="Close PDF preview"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
      <iframe
        src={pdfUrl(doc.id)}
        title={doc.title}
        className="h-[calc(100vh-3rem)] w-full bg-muted"
      />
    </div>
  )
}

function HubTopicContent({ slug, onPreviewPdf }: { slug: string; onPreviewPdf: (doc: Document) => void }) {
  const { data, isLoading, error } = useHub(slug)
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null)
  if (isLoading) return <div className="py-12 flex justify-center"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
  if (error || !data) return <p className="text-muted-foreground py-8 text-center">Content not yet available for this topic.</p>
  const sections = data.sections ?? []
  const documents = data.documents ?? []

  return (
    <div>
      {sections.length === 0 && documents.length === 0 && (
        <p className="text-muted-foreground py-8 text-center">No content yet. Run the seed script or ingest a document.</p>
      )}

      {sections.map((section, idx) => (
        <SubSection key={section.id} section={section} defaultOpen={idx === 0} />
      ))}

      {documents.length > 0 && (
        <div className="mt-8">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">
              Ingested Sources · {documents.length}
            </h3>
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <MessageSquare className="h-3 w-3" />
              Ask the chat widget below to search these
            </span>
          </div>
          <div className="space-y-2">
            {documents.map((doc) => (
              <DocumentCard
                key={doc.id}
                doc={doc}
                onPreviewPdf={onPreviewPdf}
                regenerating={regeneratingId === doc.id}
                onRegenerate={async (target) => {
                  setRegeneratingId(target.id)
                  try {
                    await postJson(`/api/documents/${target.id}/regenerate-qas`, {})
                  } catch {
                    alert('Q&A regeneration failed to start. Check backend logs.')
                  } finally {
                    setRegeneratingId(null)
                  }
                }}
              />
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
  const [previewDoc, setPreviewDoc] = useState<Document | null>(null)

  if (isLoading) return (
    <div className="flex justify-center py-20">
      <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
    </div>
  )
  if (!topics.length) return null

  const active = activeTab || topics[0]?.slug || ''

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      {/* Page header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="inline-flex items-center rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-semibold text-primary">
            Learning Hub
          </span>
        </div>
        <h1 className="text-2xl font-bold tracking-tight">Deep Dive Reference</h1>
        <p className="text-muted-foreground text-sm mt-1.5">
          Click any section to expand · Ingest documents to add sources · Ask the chat widget to search
        </p>
      </div>

      <Tabs value={active} onValueChange={setActiveTab}>
        <TabsList className="flex flex-wrap h-auto gap-1 mb-7 p-1">
          {topics.map((t) => (
            <TabsTrigger key={t.slug} value={t.slug} className="text-xs sm:text-sm px-3 py-1.5">
              {t.label}
            </TabsTrigger>
          ))}
        </TabsList>
        {topics.map((t) => (
          <TabsContent key={t.slug} value={t.slug}>
            <HubTopicContent slug={t.slug} onPreviewPdf={setPreviewDoc} />
          </TabsContent>
        ))}
      </Tabs>
      {previewDoc && <PdfPreview doc={previewDoc} onClose={() => setPreviewDoc(null)} />}
    </div>
  )
}
