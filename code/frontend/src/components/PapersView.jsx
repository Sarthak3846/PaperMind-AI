import { FileText } from 'lucide-react'
import { Card, Citations, Pill } from './ui.jsx'

const FIELDS = [
  ['objectives', 'Objectives'], ['methodology', 'Methodology'], ['datasets', 'Datasets'], ['findings', 'Findings'],
  ['quantitative_results', 'Quantitative results'], ['limitations', 'Limitations'], ['future_directions', 'Future directions'],
]

const Label = ({ children }) => <dt className="text-[11px] font-semibold uppercase tracking-[0.16em] text-indigo-300">{children}</dt>
const Missing = () => <span className="text-xs italic text-gray-600">Not reported in the retrieved passages</span>

export default function PapersView({ result, label }) {
  const list = result.paper_analyses || []
  if (!list.length) return <p className="text-sm text-gray-400">No paper analyses for this run.</p>
  const cite = (ids) => <Citations ids={ids} sources={result.sources} label={label} />
  return (
    <div className="space-y-5">
      {list.map((a) => (
        <Card key={a.paper_id} className="p-6">
          <div className="mb-1 flex flex-wrap items-center gap-3">
            <FileText className="h-5 w-5 text-indigo-300" />
            <h4 className="font-semibold text-white">{a.title}</h4>
            <Pill className="font-mono">{a.filename}</Pill>
          </div>
          <p className="mb-5 text-[11px] text-gray-500">
            Analysed from {a.chunk_ids_provided.length} retrieved passages (pages {a.pages_provided.join(', ')}), not the whole paper.
            {a.rejected_claims > 0 && ` ${a.rejected_claims} unsupported claim(s) were removed automatically.`}
          </p>

          <dl className="mb-5 rounded-xl border border-indigo-500/20 bg-indigo-500/[0.06] p-4">
            <Label>Research problem</Label>
            <dd className="mt-1.5 text-sm leading-relaxed text-gray-100">
              {a.research_problem ? <>{a.research_problem.text}{cite(a.research_problem.chunk_ids)}</> : <Missing />}
            </dd>
          </dl>

          <dl className="grid gap-x-8 gap-y-5 md:grid-cols-2">
            {FIELDS.map(([key, name]) => {
              const val = a[key]
              const empty = !val || !val.length
              return (
                <div key={key} className={key === 'quantitative_results' || key === 'findings' ? 'md:col-span-2' : ''}>
                  <Label>{name}</Label>
                  <dd className="mt-1.5 text-sm text-gray-200">
                    {empty ? <Missing /> : (
                      <ul className="list-disc space-y-1.5 pl-5 marker:text-indigo-400/60">
                        {val.map((c, i) => key === 'quantitative_results'
                          ? <li key={i}><b className="text-white">{c.metric}:</b> {c.value}{c.context ? ` (${c.context})` : ''}{cite(c.chunk_ids)}</li>
                          : <li key={i}>{c.text}{cite(c.chunk_ids)}</li>)}
                      </ul>
                    )}
                  </dd>
                </div>
              )
            })}
          </dl>
        </Card>
      ))}
    </div>
  )
}
