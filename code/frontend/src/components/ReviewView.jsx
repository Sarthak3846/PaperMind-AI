import { Citations, SectionTitle, StatusBadge } from './ui.jsx'

const SECTIONS = [
  ['research_overview', 'Research overview'],
  ['paper_summaries', 'Individual paper summaries'],
  ['cross_paper_synthesis', 'Cross-paper synthesis'],
  ['agreements_and_contradictions', 'Agreements and contradictions'],
  ['research_gaps', 'Research gaps'],
  ['limitations', 'Limitations'],
  ['conclusion', 'Conclusion'],
]

const SEGMENTS = [
  ['supported', 'bg-emerald-500', 'text-emerald-300', 'supported'],
  ['partially_supported', 'bg-amber-500', 'text-amber-300', 'partial'],
  ['unsupported', 'bg-red-500', 'text-red-300', 'unsupported'],
  ['unverified', 'bg-slate-500', 'text-gray-400', 'unverified'],
]

function Statement({ s, sources, label }) {
  return (
    <li className="rounded-xl border border-transparent px-3 py-2 leading-relaxed text-gray-200 transition-colors hover:border-white/10 hover:bg-white/[0.03]">
      <span className={s.meta ? 'italic text-gray-400' : ''}>{s.text}</span>
      <Citations ids={s.chunk_ids} sources={sources} label={label} />
      {s.meta
        ? <span className="ml-2 text-[11px] text-gray-500">(scope note, no citation needed)</span>
        : <span className="ml-2 align-middle"><StatusBadge status={s.status} reason={s.status_reason} /></span>}
      {s.status && s.status !== 'supported' && s.status_reason && <div className="mt-1 text-xs text-gray-500">↳ {s.status_reason}</div>}
    </li>
  )
}

export default function ReviewView({ result, label, title }) {
  const r = result.review
  if (!r) return <p className="text-sm text-gray-400">No literature review was generated for this run.</p>
  const v = result.verification
  const list = (items) => <ul className="space-y-1">{items.map((s) => <Statement key={s.sid} s={s} sources={result.sources} label={label} />)}</ul>
  return (
    <div>
      {v && (
        <div className="mb-8 rounded-2xl border border-white/10 bg-black/20 p-4">
          <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
            <span className="text-sm font-semibold text-white">Citation verification</span>
            <span className="text-xs text-gray-500">{v.checked} claims checked</span>
          </div>
          <div className="flex h-2.5 overflow-hidden rounded-full bg-white/5" role="img" aria-label="Verification breakdown">
            {SEGMENTS.map(([k, bar]) => v[k] > 0 && <div key={k} className={`${bar} transition-all duration-700`} style={{ width: `${(v[k] / (v.checked || 1)) * 100}%` }} />)}
          </div>
          <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs">
            {SEGMENTS.map(([k, , text, name]) => <span key={k} className={text}>{v[k]} {name}</span>)}
          </div>
          <p className="mt-2 text-xs text-gray-500">Flagged claims are shown, not hidden. Treat anything not marked “Supported” as unverified until you read the cited page.</p>
        </div>
      )}

      {SECTIONS.map(([key, name]) => {
        const val = r[key]
        if (!val || !val.length) return null
        return (
          <div key={key} className="mt-8 first:mt-0">
            <SectionTitle>{name}</SectionTitle>
            {key === 'paper_summaries'
              ? val.map((p) => (
                  <div key={p.paper_id} className="mb-4">
                    <div className="mb-1 px-3 text-sm font-semibold text-indigo-200">{title(p.paper_id)}</div>
                    {list(p.statements)}
                  </div>
                ))
              : list(val)}
          </div>
        )
      })}

      <div className="mt-10">
        <SectionTitle hint="Page numbers refer to the PDF page of the paper in DATASET/">References</SectionTitle>
        <ol className="space-y-2 text-xs text-gray-400">
          {(result.references || []).map((x) => (
            <li key={x.chunk_id} className="flex gap-3 rounded-lg px-3 py-1.5 hover:bg-white/[0.03]">
              <span className="font-mono text-indigo-300">[{x.ref}]</span>
              <span>{x.title} <span className="block font-mono text-[11px] text-gray-600">{x.filename} · page {x.page} · {x.chunk_id}</span></span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  )
}
