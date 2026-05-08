'use client'
import { useRef, useState } from 'react'
import { Upload, Link2, FileText, CheckCircle2, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import TopicSelector from '@/components/ingest/TopicSelector'
import IngestStatus from '@/components/ingest/IngestStatus'
import { useTopics, postForm, postJson } from '@/lib/api'

export default function IngestPage() {
  const { data: topics = [] } = useTopics()
  const [pdfTopics, setPdfTopics] = useState<string[]>([])
  const [urlTopics, setUrlTopics] = useState<string[]>([])
  const [url, setUrl] = useState('')
  const [pdfDocId, setPdfDocId] = useState<string | null>(null)
  const [urlDocId, setUrlDocId] = useState<string | null>(null)
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  const submitPdf = async () => {
    if (!pdfFile) return
    setSubmitting(true)
    try {
      const form = new FormData()
      form.append('file', pdfFile)
      form.append('topic_ids', pdfTopics.join(','))
      form.append('generate_qa', 'true')
      const res = await postForm<{ doc_id: string }>('/api/ingest/pdf', form)
      setPdfDocId(res.doc_id)
      setPdfFile(null)
      setPdfTopics([])
    } catch {
      alert('Upload failed. Check backend connection.')
    } finally {
      setSubmitting(false)
    }
  }

  const submitUrl = async () => {
    if (!url.trim()) return
    setSubmitting(true)
    try {
      const res = await postJson<{ doc_id: string }>('/api/ingest/url', {
        url: url.trim(),
        topic_ids: urlTopics,
        generate_qa: true,
      })
      setUrlDocId(res.doc_id)
      setUrl('')
      setUrlTopics([])
    } catch {
      alert('URL ingestion failed. Check backend connection.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Ingest Documents</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Upload PDFs or add article URLs. Codex auto-generates Q&amp;A pairs in the background.
          Topics are auto-detected if you leave them blank.
        </p>
      </div>

      {/* PDF Upload */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <FileText className="h-4 w-4" /> Upload PDF
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div
            className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:bg-muted/50 transition-colors"
            onClick={() => fileRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault()
              const f = e.dataTransfer.files[0]
              if (f?.type === 'application/pdf') setPdfFile(f)
            }}
          >
            {pdfFile ? (
              <div className="flex items-center justify-center gap-2 text-sm">
                <CheckCircle2 className="h-4 w-4 text-green-600" />
                <span className="font-medium">{pdfFile.name}</span>
                <span className="text-muted-foreground">({(pdfFile.size / 1024).toFixed(0)} KB)</span>
              </div>
            ) : (
              <>
                <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                <p className="text-sm text-muted-foreground">Drag &amp; drop or tap to choose a PDF</p>
              </>
            )}
          </div>
          <input ref={fileRef} type="file" accept=".pdf" className="hidden" onChange={(e) => setPdfFile(e.target.files?.[0] || null)} />
          <TopicSelector topics={topics} selected={pdfTopics} onChange={setPdfTopics} />
          {pdfTopics.length === 0 && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Sparkles className="h-3 w-3" />
              Topics will be auto-detected from document content
            </div>
          )}
          <Button className="w-full" onClick={submitPdf} disabled={!pdfFile || submitting}>
            {submitting ? 'Processing…' : 'Process PDF'}
          </Button>
          {pdfDocId && <IngestStatus docId={pdfDocId} />}
        </CardContent>
      </Card>

      <Separator />

      {/* URL Ingestion */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Link2 className="h-4 w-4" /> Add Article URL
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Input
            type="url"
            placeholder="https://arxiv.org/abs/..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
          <TopicSelector topics={topics} selected={urlTopics} onChange={setUrlTopics} />
          {urlTopics.length === 0 && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Sparkles className="h-3 w-3" />
              Topics will be auto-detected from page content
            </div>
          )}
          <Button className="w-full" onClick={submitUrl} disabled={!url.trim() || submitting}>
            {submitting ? 'Processing…' : 'Process URL'}
          </Button>
          {urlDocId && <IngestStatus docId={urlDocId} />}
        </CardContent>
      </Card>
    </div>
  )
}
