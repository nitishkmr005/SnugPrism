'use client'
import { useState } from 'react'
import { MessageCircle, X, Maximize2, Minimize2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import ChatPanel from './ChatPanel'

export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [fullscreen, setFullscreen] = useState(false)

  if (fullscreen) {
    return (
      <div className="fixed inset-0 z-50 bg-background flex flex-col">
        <div className="flex items-center justify-between px-6 py-3.5 border-b bg-muted/40 shrink-0">
          <div>
            <p className="font-semibold text-sm">SnugPrism AI Coach</p>
            <p className="text-xs text-muted-foreground">RAG · Web Search · Code</p>
          </div>
          <div className="flex items-center gap-1">
            <button
              type="button"
              onClick={() => setFullscreen(false)}
              className="inline-flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
              title="Exit full screen"
            >
              <Minimize2 className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => { setFullscreen(false); setOpen(false) }}
              className="inline-flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
              title="Close"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
        <div className="flex-1 overflow-hidden max-w-3xl w-full mx-auto px-4 py-2">
          <ChatPanel />
        </div>
      </div>
    )
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
      {open && (
        <div className="w-[360px] sm:w-[420px] h-[560px] rounded-2xl border shadow-2xl bg-background flex flex-col overflow-hidden animate-in slide-in-from-bottom-4 duration-200">
          <div className="flex items-center justify-between px-4 py-3 border-b bg-muted/40 shrink-0">
            <div>
              <p className="font-semibold text-sm">SnugPrism AI Coach</p>
              <p className="text-xs text-muted-foreground">RAG · Web Search · Code</p>
            </div>
            <div className="flex items-center gap-1">
              <button
                type="button"
                onClick={() => setFullscreen(true)}
                className="inline-flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
                title="Full screen"
              >
                <Maximize2 className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                onClick={() => setOpen(false)}
                className="inline-flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
                title="Close"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
          <div className="flex-1 overflow-hidden">
            <ChatPanel />
          </div>
        </div>
      )}
      <Button
        size="icon"
        className="h-14 w-14 rounded-full shadow-xl ring-2 ring-primary/10 hover:ring-primary/30 transition-all"
        onClick={() => setOpen((o) => !o)}
        aria-label="Toggle chat"
      >
        {open ? <X className="h-5 w-5" /> : <MessageCircle className="h-5 w-5" />}
      </Button>
    </div>
  )
}
