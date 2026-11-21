import { AlertTriangle, Info } from 'lucide-react'
import { Card, Citations, Pill, StatusBadge } from './ui.jsx'

export default function GapsView({ result, label }) {
  const g = result.gaps
  if (!g) return <p className="text-sm text-gray-400">No gap analysis for this run.</p>
  return (
    <div className="space-y-4">
      <Card className="flex gap-3 border-indigo-500/30 bg-indigo-500/[0.06]">
        <Info className="mt-0.5 h-4 w-4 shrink-0 text-indigo-300" />
        <p className="text-xs leading-relaxed text-gray-300">{g.scope_disclaimer}</p>
      </Card>
      {g.gaps.length === 0 && <p className="text-sm text-gray-400">No gaps could be supported by the analysed papers.</p>}
      {g.gaps.map((x) => (
        <Card key={x.gap_id} className="p-6 transition-colors hover:bg-white/[0.05]">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <span className="rounded-md bg-white/5 px-1.5 py-0.5 font-mono text-xs text-gray-400">{x.gap_id}</span>
            <h4 className="font-semibold text-white">{x.title}</h4>
            <Pill tone={x.basis === 'explicit' ? 'emerald' : 'amber'}>{x.basis === 'explicit' ? 'Explicit: stated by the authors' : 'Inferred: research opportunity'}</Pill>
            <StatusBadge status={x.status} reason={x.status_reason} />
          </div>
          <p className="text-sm leading-relaxed text-gray-200">{x.description}</p>
          <p className="mt-3 text-sm leading-relaxed text-gray-400"><b className="text-gray-300">Why it exists:</b> {x.why_it_exists}</p>
          <div className="mt-4 flex flex-wrap items-center gap-1.5 text-xs text-gray-500">
            Supporting papers: {x.supporting_paper_ids.map((p) => <Pill key={p} tone="indigo">{label(p)}</Pill>)}
            <Citations ids={x.chunk_ids} sources={result.sources} label={label} />
          </div>
          {x.note && <p className="mt-3 flex items-start gap-2 text-xs text-amber-300"><AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />{x.note}</p>}
        </Card>
      ))}
    </div>
  )
}
