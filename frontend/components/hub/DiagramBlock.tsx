'use client'
import { useEffect, useRef } from 'react'

export default function DiagramBlock({ definition }: { definition: string }) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current || !definition) return
    import('mermaid').then((m) => {
      m.default.initialize({ startOnLoad: false, theme: 'default', securityLevel: 'loose' })
      const id = `mmd-${Math.random().toString(36).slice(2)}`
      m.default.render(id, definition).then(({ svg }) => {
        if (ref.current) ref.current.innerHTML = svg
      }).catch(() => {
        if (ref.current) ref.current.innerHTML = `<pre class="text-xs text-muted-foreground">${definition}</pre>`
      })
    })
  }, [definition])

  return <div ref={ref} className="my-4 flex justify-center overflow-x-auto" />
}
