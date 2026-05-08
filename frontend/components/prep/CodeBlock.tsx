'use client'
import { useState } from 'react'
import { Check, Copy } from 'lucide-react'
import SyntaxHighlighter from 'react-syntax-highlighter'
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs'

interface CodeBlockProps {
  code: string
  language?: string
}

export default function CodeBlock({ code, language = 'python' }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    await navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // Strip markdown fences if present
  const clean = code.replace(/^```[\w]*\n?/, '').replace(/```\s*$/, '').trim()
  const lang = code.match(/^```(\w+)/)?.[1] || language

  return (
    <div className="relative rounded-lg overflow-hidden text-sm my-3 border">
      <div className="flex items-center justify-between bg-zinc-900 px-3 py-1.5">
        <span className="text-xs text-zinc-400">{lang}</span>
        <button onClick={copy} className="text-zinc-400 hover:text-zinc-200 transition-colors">
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
        </button>
      </div>
      <SyntaxHighlighter
        language={lang}
        style={atomOneDark}
        customStyle={{ margin: 0, borderRadius: 0, padding: '1rem' }}
        wrapLongLines
      >
        {clean}
      </SyntaxHighlighter>
    </div>
  )
}
