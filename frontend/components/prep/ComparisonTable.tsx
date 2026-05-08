import type { ComparisonTable as CompTableType } from '@/lib/types'

export default function ComparisonTable({ table }: { table: CompTableType }) {
  return (
    <div className="overflow-x-auto my-3 rounded-md border text-sm">
      <table className="w-full text-left">
        <thead className="bg-muted">
          <tr>
            {table.headers.map((h, i) => (
              <th key={i} className="px-3 py-2 font-semibold text-xs uppercase tracking-wide text-muted-foreground">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, ri) => (
            <tr key={ri} className="border-t hover:bg-muted/30 transition-colors">
              {row.map((cell, ci) => (
                <td key={ci} className="px-3 py-2 text-sm">
                  {cell}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
