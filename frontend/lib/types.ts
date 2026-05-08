export interface Topic {
  id: string
  slug: string
  label: string
  sort_order: number
}

export interface PDFLink {
  doc_id: string
  page: number
  label: string
}

export interface ComparisonTable {
  headers: string[]
  rows: string[][]
}

export interface Question {
  id: string
  topic: Topic
  question: string
  answer: string
  difficulty: 'easy' | 'medium' | 'hard'
  tags: string[]
  code_snippet: string | null
  comparison_table: ComparisonTable | null
  reference_urls: string[]
  pdf_links: PDFLink[]
  source: string
  created_at: string
}

export interface QuestionsPage {
  items: Question[]
  total: number
}

export interface SourceChunk {
  chunk_id: string
  score: number
  content_preview: string
  doc_title: string
}

export interface ArticleResult {
  title: string
  url: string
  snippet: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: SourceChunk[]
  articles?: ArticleResult[]
}

export interface HubSection {
  id: string
  title: string
  content: string
  sort_order: number
  diagram_def: string | null
}

export interface HubResponse {
  topic: Topic
  sections: HubSection[]
  documents: Document[]
}

export interface Document {
  id: string
  title: string
  source_type: 'pdf' | 'url'
  source_ref: string
  topic_ids: string[]
  chunk_count: number
  ingested_at: string
}

export interface IngestStatus {
  doc_id: string
  status: 'processing' | 'done' | 'failed'
  chunk_count: number
  qa_count: number
  error?: string
}

export interface RunLogEntry {
  id: string
  timestamp: string
  call_type: 'llm' | 'embedding'
  model: string
  purpose: string
  input_tokens: number
  output_tokens: number
  cost_usd: number
}

export interface ModelBreakdown {
  calls: number
  input_tokens: number
  output_tokens: number
  cost_usd: number
}

export interface PurposeBreakdown {
  calls: number
  cost_usd: number
}

export interface RunSummary {
  total_cost_usd: number
  total_calls: number
  total_input_tokens: number
  total_output_tokens: number
  by_model: Record<string, ModelBreakdown>
  by_purpose: Record<string, PurposeBreakdown>
  entries: RunLogEntry[]
  pricing: Record<string, { input: number; output: number }>
}
