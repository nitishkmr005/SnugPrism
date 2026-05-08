import { useQuery } from '@tanstack/react-query'
import type { Topic, QuestionsPage, HubResponse, Document, IngestStatus, RunSummary } from './types'

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`)
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`)
  return res.json()
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`)
  return res.json()
}

export async function postForm<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${API}${path}`, { method: 'POST', body: form })
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`)
  return res.json()
}

export function useTopics() {
  return useQuery<Topic[]>({
    queryKey: ['topics'],
    queryFn: () => get('/api/topics'),
    staleTime: Infinity,
  })
}

export function useQuestions(params: {
  topic_slug?: string
  difficulty?: string
  q?: string
  limit?: number
  offset?: number
}) {
  const search = new URLSearchParams()
  if (params.topic_slug) search.set('topic_slug', params.topic_slug)
  if (params.difficulty) search.set('difficulty', params.difficulty)
  if (params.q) search.set('q', params.q)
  if (params.limit) search.set('limit', String(params.limit))
  if (params.offset) search.set('offset', String(params.offset))
  const qs = search.toString()
  return useQuery<QuestionsPage>({
    queryKey: ['questions', params],
    queryFn: () => get(`/api/questions${qs ? '?' + qs : ''}`),
  })
}

export function useHub(slug: string) {
  return useQuery<HubResponse>({
    queryKey: ['hub', slug],
    queryFn: () => get(`/api/hub/${slug}`),
    enabled: !!slug,
  })
}

export function useDocuments() {
  return useQuery<Document[]>({
    queryKey: ['documents'],
    queryFn: () => get('/api/documents'),
  })
}

export function useIngestStatus(docId: string | null) {
  return useQuery<IngestStatus>({
    queryKey: ['ingest-status', docId],
    queryFn: () => get(`/api/ingest/status/${docId}`),
    enabled: !!docId,
    refetchInterval: (q) => {
      const data = q.state.data
      if (data && (data.status === 'done' || data.status === 'failed')) return false
      return 2000
    },
  })
}

export function useRunSummary() {
  return useQuery<RunSummary>({
    queryKey: ['run-summary'],
    queryFn: () => get('/api/run-summary'),
    refetchInterval: 30_000,
  })
}

export function streamChat(
  message: string,
  sessionId: string | null,
  onToken: (t: string) => void,
  onDone: (meta: { sources: unknown[]; articles: unknown[]; session_id: string }) => void,
  onError: (e: Error) => void
): void {
  const body = JSON.stringify({
    message,
    session_id: sessionId,
    stream: true,
    include_web_search: true,
  })
  const ctrl = new AbortController()

  fetch(`${API}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
    signal: ctrl.signal,
  }).then(async (res) => {
    if (!res.ok || !res.body) { onError(new Error('Chat request failed')); return }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buf = ''
    let sources: unknown[] = []
    let articles: unknown[] = []
    let sessionIdOut = sessionId || ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const lines = buf.split('\n')
      buf = lines.pop() || ''
      let eventType = ''
      for (const line of lines) {
        if (line.startsWith('event: ')) { eventType = line.slice(7).trim(); continue }
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (eventType === 'token') onToken(JSON.parse(data))
          else if (eventType === 'sources') sources = JSON.parse(data)
          else if (eventType === 'articles') articles = JSON.parse(data)
          else if (eventType === 'session') sessionIdOut = JSON.parse(data).session_id
          else if (eventType === 'done') onDone({ sources, articles, session_id: sessionIdOut })
        }
      }
    }
  }).catch(onError)
}
