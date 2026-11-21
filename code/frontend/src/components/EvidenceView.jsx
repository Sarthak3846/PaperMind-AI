import { Card, Citations, Pill, SectionTitle } from './ui.jsx'

export default function EvidenceView({ result, label }) {
  const r = result.retrieval
  const critic = result.critic
  return (
    <div className="space-y-8">
      {r && (
        <div>
          <SectionTitle>Retrieval</SectionTitle>
          <p className="text-xs text-gray-400">Search terms: <span className="font-mono text-gray-300">{r.terms.join(', ')}</span> · {r.n_hits} passages</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {r.papers.map((p) => <Pill key={p.paper_id} tone="indigo">{label(p.paper_id)}: {p.hits} hits (top BM25 {p.top_score})</Pill>)}
          </div>
        </div>
      )}

      <div>
        <SectionTitle hint="Quotes were checked character-by-character against the source chunk before being accepted.">Validated evidence ({result.evidence?.length || 0})</SectionTitle>
        <div className="space-y-3">
          {(result.evidence || []).map((e) => (
            <Card key={e.evidence_id} className="py-4 transition-colors hover:bg-white/[0.05]">
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <Pill className="font-mono">{e.evidence_id}</Pill><Pill tone="indigo">{e.kind}</Pill>
                <span className="text-gray-500">{label(e.paper_id)} · p.{e.page}</span>
              </div>
              <p className="mt-2 text-sm text-gray-200">{e.claim}</p>
              <blockquote className="mt-2 border-l-2 border-indigo-400/40 pl-3 text-xs italic leading-relaxed text-gray-400">
                “{e.quote}”<Citations ids={[e.chunk_id]} sources={result.sources} label={label} />
              </blockquote>
            </Card>
          ))}
        </div>
      </div>

      {critic && (critic.flagged.length > 0 || critic.contradictions.length > 0 || critic.missing_information.length > 0) && (
        <div>
          <SectionTitle>Critic findings</SectionTitle>
          <ul className="list-disc space-y-1.5 pl-5 text-sm text-gray-300 marker:text-red-400/60">
            {critic.flagged.map((f) => <li key={f.evidence_id}><b className="font-mono text-gray-200">{f.evidence_id}</b> flagged: {f.reason}</li>)}
            {critic.contradictions.map((c, i) => <li key={`c${i}`}>Possible contradiction: {c}</li>)}
            {critic.missing_information.map((m, i) => <li key={`m${i}`}>Missing: {m}</li>)}
          </ul>
        </div>
      )}

      {result.rejected_evidence?.length > 0 && (
        <div>
          <SectionTitle hint="Rejected automatically; never shown to later agents.">Rejected evidence ({result.rejected_evidence.length})</SectionTitle>
          <ul className="list-disc space-y-1 pl-5 text-xs text-gray-500">
            {result.rejected_evidence.map((e, i) => <li key={i}>{e.reason}: {e.claim}</li>)}
          </ul>
        </div>
      )}
    </div>
  )
}
