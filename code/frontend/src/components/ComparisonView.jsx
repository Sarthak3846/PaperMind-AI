import { Card, Citations, Pill, SectionTitle } from './ui.jsx'

const DIM = { methodology: 'Methodology', datasets: 'Datasets', evaluation_metrics: 'Evaluation metrics', findings: 'Findings' }

function StatementList({ items, result, label }) {
  return (
    <ul className="list-disc space-y-2 pl-5 text-sm text-gray-200 marker:text-indigo-400/60">
      {items.map((s, i) => (
        <li key={i}>{s.text}
          <span className="ml-1 text-[11px] text-gray-500">({s.paper_ids.map(label).join(' vs ')})</span>
          <Citations ids={s.chunk_ids} sources={result.sources} label={label} />
        </li>
      ))}
    </ul>
  )
}

export default function ComparisonView({ result, label, title }) {
  const c = result.comparison
  if (!c) return <p className="text-sm text-gray-400">No comparison for this run.</p>
  if (c.skipped) {
    return <Card className="border-amber-500/30 bg-amber-500/[0.05]"><p className="text-sm font-semibold text-amber-300">Comparison skipped</p><p className="mt-1 text-sm text-gray-400">{c.skip_reason}</p></Card>
  }
  const papers = (result.paper_analyses || []).map((a) => a.paper_id)
  return (
    <div className="space-y-8">
      <Card className={c.comparable ? 'border-emerald-500/20' : 'border-amber-500/40'}>
        <div className="mb-2"><Pill tone={c.comparable ? 'emerald' : 'amber'}>{c.comparable ? 'Directly comparable' : 'Not directly comparable'}</Pill></div>
        <p className="text-sm leading-relaxed text-gray-300">{c.comparability_notes || 'No comparability notes returned.'}</p>
      </Card>

      {c.table.length > 0 && (
        <div>
          <SectionTitle>Comparison table</SectionTitle>
          <div className="scroll-thin overflow-x-auto rounded-2xl border border-white/10">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="bg-white/[0.04] text-[11px] uppercase tracking-wider text-gray-400">
                <tr><th className="p-4">Dimension</th>{papers.map((p) => <th key={p} className="p-4">{label(p)}</th>)}</tr>
              </thead>
              <tbody>
                {c.table.map((row) => (
                  <tr key={row.dimension} className="border-t border-white/5 align-top transition-colors hover:bg-white/[0.02]">
                    <td className="p-4 font-medium text-indigo-200">{DIM[row.dimension]}</td>
                    {papers.map((p) => {
                      const e = row.entries.find((x) => x.paper_id === p)
                      return (
                        <td key={p} className="p-4 text-gray-200">
                          {e ? <>{e.value}<Citations ids={e.chunk_ids} sources={result.sources} label={label} /></> : <span className="text-xs italic text-gray-600">not reported</span>}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {c.similarities.length > 0 && <div><SectionTitle>Similarities</SectionTitle><StatementList items={c.similarities} result={result} label={label} /></div>}
      {c.differences.length > 0 && <div><SectionTitle>Differences</SectionTitle><StatementList items={c.differences} result={result} label={label} /></div>}

      <div>
        <SectionTitle hint="A difference caused by different tasks, datasets or settings is not a contradiction.">Contradictions</SectionTitle>
        {c.contradictions.length === 0 && <p className="text-sm text-gray-500">No contradictions were identified in the retrieved passages.</p>}
        <div className="space-y-3">
          {c.contradictions.map((x, i) => (
            <Card key={i} className={x.conditions_comparable ? 'border-red-500/30 bg-red-500/[0.04]' : 'border-amber-500/30 bg-amber-500/[0.04]'}>
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <span className="font-medium text-white">{x.topic}</span>
                <Pill tone={x.conditions_comparable ? 'red' : 'amber'}>{x.conditions_comparable ? 'Comparable conditions' : 'Conditions differ: not a true contradiction'}</Pill>
              </div>
              <ul className="space-y-1.5 text-sm text-gray-200">
                {x.positions.map((p, j) => <li key={j}><b className="text-indigo-200">{label(p.paper_id)}:</b> {p.statement}<Citations ids={p.chunk_ids} sources={result.sources} label={label} /></li>)}
              </ul>
              {x.explanation && <p className="mt-3 text-xs text-gray-400">{x.explanation}</p>}
            </Card>
          ))}
        </div>
      </div>

      {c.incompatibilities.length > 0 && (
        <div>
          <SectionTitle>Studies not compared (incompatible conditions)</SectionTitle>
          <ul className="list-disc space-y-1 pl-5 text-sm text-gray-300">
            {c.incompatibilities.map((x, i) => <li key={i}>{x.paper_ids.map(title).join(' / ')}: {x.reason}</li>)}
          </ul>
        </div>
      )}
      {c.rejected_items > 0 && <p className="text-xs text-gray-500">{c.rejected_items} comparison item(s) were removed automatically because they cited unknown sources.</p>}
    </div>
  )
}
