'use client'
import type { RunSummary } from '@/lib/types'

const PURPOSES: Record<string, string> = {
  chat: 'Chat',
  qa_generation: 'Q&A Gen',
  topic_detection: 'Topic Detect',
  embedding: 'Embedding',
  hub_generation: 'Hub Gen',
}

function usd(n: number) {
  return n < 0.001 ? `$${n.toFixed(6)}` : `$${n.toFixed(4)}`
}

function num(n: number) {
  return n.toLocaleString()
}

function dateTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

interface Props {
  data: RunSummary
}

export default function RunSummaryTable({ data }: Props) {
  return (
    <div className="space-y-8">
      {/* Top-line stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: 'Total Cost', value: usd(data.total_cost_usd) },
          { label: 'API Calls', value: num(data.total_calls) },
          { label: 'Input Tokens', value: num(data.total_input_tokens) },
          { label: 'Output Tokens', value: num(data.total_output_tokens) },
        ].map(({ label, value }) => (
          <div key={label} className="rounded-lg border p-4">
            <p className="text-xs text-muted-foreground mb-1">{label}</p>
            <p className="text-xl font-bold tabular-nums">{value}</p>
          </div>
        ))}
      </div>

      {/* By model */}
      <div>
        <h2 className="text-sm font-semibold mb-3">By Model</h2>
        <div className="rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                {['Model', 'Calls', 'Input', 'Output', 'Cost'].map((h) => (
                  <th key={h} className="px-4 py-2 text-left font-medium text-muted-foreground">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y">
              {Object.entries(data.by_model)
                .sort((a, b) => b[1].cost_usd - a[1].cost_usd)
                .map(([model, stats]) => (
                  <tr key={model} className="hover:bg-muted/20">
                    <td className="px-4 py-2 font-mono text-xs">{model}</td>
                    <td className="px-4 py-2 tabular-nums">{num(stats.calls)}</td>
                    <td className="px-4 py-2 tabular-nums">{num(stats.input_tokens)}</td>
                    <td className="px-4 py-2 tabular-nums">{num(stats.output_tokens)}</td>
                    <td className="px-4 py-2 tabular-nums font-medium">{usd(stats.cost_usd)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* By purpose */}
      <div>
        <h2 className="text-sm font-semibold mb-3">By Purpose</h2>
        <div className="rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted/50">
              <tr>
                {['Purpose', 'Calls', 'Cost'].map((h) => (
                  <th key={h} className="px-4 py-2 text-left font-medium text-muted-foreground">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y">
              {Object.entries(data.by_purpose)
                .sort((a, b) => b[1].cost_usd - a[1].cost_usd)
                .map(([purpose, stats]) => (
                  <tr key={purpose} className="hover:bg-muted/20">
                    <td className="px-4 py-2">{PURPOSES[purpose] ?? purpose}</td>
                    <td className="px-4 py-2 tabular-nums">{num(stats.calls)}</td>
                    <td className="px-4 py-2 tabular-nums font-medium">{usd(stats.cost_usd)}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Full log */}
      <div>
        <h2 className="text-sm font-semibold mb-3">Call Log <span className="text-muted-foreground font-normal">({data.entries.length} entries, newest first)</span></h2>
        <div className="rounded-lg border overflow-auto max-h-[420px]">
          <table className="w-full text-xs">
            <thead className="bg-muted/50 sticky top-0">
              <tr>
                {['Time', 'Type', 'Model', 'Purpose', 'In', 'Out', 'Cost'].map((h) => (
                  <th key={h} className="px-3 py-2 text-left font-medium text-muted-foreground whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y">
              {data.entries.map((e) => (
                <tr key={e.id} className="hover:bg-muted/20">
                  <td className="px-3 py-1.5 text-muted-foreground whitespace-nowrap">
                    {dateTime(e.timestamp)}
                  </td>
                  <td className="px-3 py-1.5 capitalize">{e.call_type}</td>
                  <td className="px-3 py-1.5 font-mono">{e.model}</td>
                  <td className="px-3 py-1.5">{PURPOSES[e.purpose] ?? e.purpose}</td>
                  <td className="px-3 py-1.5 tabular-nums">{num(e.input_tokens)}</td>
                  <td className="px-3 py-1.5 tabular-nums">{num(e.output_tokens)}</td>
                  <td className="px-3 py-1.5 tabular-nums font-medium">{usd(e.cost_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
