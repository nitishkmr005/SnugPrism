'use client'
import { useEffect, useRef, useState } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import ChatMessage from './ChatMessage'
import type { ChatMessage as ChatMsg, ArticleResult, SourceChunk } from '@/lib/types'
import { streamChat } from '@/lib/api'

export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMsg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [streamingText, setStreamingText] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingText])

  const send = () => {
    const msg = input.trim()
    if (!msg || loading) return
    setInput('')
    setLoading(true)
    setMessages((prev) => [...prev, { role: 'user', content: msg }])
    setStreamingText('')

    streamChat(
      msg,
      sessionId,
      (token) => setStreamingText((prev) => prev + token),
      ({ sources, articles, session_id }) => {
        setSessionId(session_id)
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: streamingText + '',
            sources: sources as SourceChunk[],
            articles: articles as ArticleResult[],
          },
        ])
        setStreamingText('')
        setLoading(false)
      },
      () => {
        setLoading(false)
        setStreamingText('')
      }
    )
  }

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 px-3 pt-3">
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground text-sm py-8">
            <p className="font-medium">Ask me anything about DS interviews</p>
            <p className="text-xs mt-1">Try: &ldquo;Explain two-tower recommender&rdquo;</p>
          </div>
        )}
        {messages.map((m, i) => (
          <ChatMessage key={i} msg={m} />
        ))}
        {streamingText && (
          <div className="flex justify-start mb-3">
            <div className="max-w-[85%] rounded-2xl px-4 py-2.5 text-sm bg-muted">
              <p className="whitespace-pre-wrap">{streamingText}</p>
              <span className="inline-block w-1.5 h-4 bg-primary animate-pulse ml-0.5 align-middle" />
            </div>
          </div>
        )}
        {loading && !streamingText && (
          <div className="flex justify-start mb-3">
            <div className="rounded-2xl px-4 py-3 bg-muted">
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </ScrollArea>

      <div className="p-3 border-t">
        <div className="flex gap-2 items-end">
          <Textarea
            rows={2}
            className="resize-none text-sm"
            placeholder="Ask a question…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
          />
          <Button size="icon" onClick={send} disabled={!input.trim() || loading} className="shrink-0">
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-1 text-center">Enter to send · Shift+Enter for newline</p>
      </div>
    </div>
  )
}
