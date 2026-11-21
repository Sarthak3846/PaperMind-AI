import { AlertTriangle, BookOpenText, CheckCircle2, Clock, Database, Download, FileText, GitCompare, Lightbulb, XCircle } from 'lucide-react'
import { GlassCard, Pill } from './ui.jsx'
import ReviewView from './ReviewView.jsx'
import PapersView from './PapersView.jsx'
import ComparisonView from './ComparisonView.jsx'
import GapsView from './GapsView.jsx'
import EvidenceView from './EvidenceView.jsx'

const TABS = [
  { key: 'review', name: 'Literature review', Icon: BookOpenText },
  { key: 'papers', name: 'Paper analysis', Icon: FileText },
  { key: 'comparison', name: 'Comparison', Icon: GitCompare },
  { key: 'gaps', name: 'Research gaps', Icon: Lightbulb },
  { key: 'evidence', name: 'Evidence & retrieval', Icon: Database },
]

const BANNER = {
  completed: { cls: 'border-emerald-500/40 from-emerald-500/15 to-blue-500/10', text: 'text-emerald-200', Icon: CheckCircle2, icon: 'bg-emerald-500 shadow-emerald-500/30' },
  insufficient_evidence: { cls: 'border-amber-500/40 from-amber-500/15 to-orange-500/10', text: 'text-amber-200', Icon: AlertTriangle, icon: 'bg-amber-500 shadow-amber-500/30' },
  failed: { cls: 'border-red-500/40 from-red-500/15 to-purple-500/10', text: 'text-red-200', Icon: XCircle, icon: 'bg-red-500 shadow-red-500/30' },
}

export default function ResultPanel({ result, tab, onTab, label, title, onDownload }) {
  const b = BANNER[result.status] || BANNER.failed
  const hasContent = result.review || result.paper_analyses?.length > 0 || result.evidence?.length > 0
  return (
    <div className="animate-fade-in-up space-y-4">
      <div className={`flex items-center gap-4 rounded-2xl border bg-gradient-to-r p-4 ${b.cls}`}>
        <div className={`rounded-full p-2.5 text-white shadow-lg ${b.icon}`}><b.Icon className="h-5 w-5" /></div>
        <div className="min-w-0 flex-1">
          <h3 className={`text-sm font-bold capitalize ${b.text}`}>{result.status.replace('_', ' ')}</h3>
          <p className="text-sm text-gray-300">{result.message}</p>
        </div>
        {result.metrics && (
          <div className="hidden shrink-0 flex-col items-end gap-1 sm:flex">
            <Pill><Clock className="h-3 w-3" />{result.metrics.elapsed_seconds}s</Pill>
            <Pill>{result.metrics.llm_calls} LLM calls</Pill>
          </div>
        )}
      </div>

      {result.warnings?.length > 0 && (
        <ul className="space-y-1 rounded-2xl border border-amber-500/25 bg-amber-500/5 p-4 text-xs text-amber-200">
          {result.warnings.map((w, i) => <li key={i} className="flex gap-2"><AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />{w}</li>)}
        </ul>
      )}

      {hasContent && (
        <GlassCard className="p-2 md:p-3">
          <div className="flex flex-wrap items-center gap-1 border-b border-white/5 p-1 pb-3" role="tablist">
            {TABS.map((t) => (
              <button key={t.key} role="tab" aria-selected={tab === t.key} onClick={() => onTab(t.key)}
                className={`flex items-center gap-2 rounded-full px-3.5 py-2 text-sm font-medium transition-all duration-200 ${tab === t.key ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-900/40' : 'text-gray-400 hover:bg-white/5 hover:text-white'}`}>
                <t.Icon className="h-4 w-4" /><span className="hidden sm:inline">{t.name}</span>
              </button>
            ))}
            {result.review && (
              <button onClick={onDownload} className="ml-auto flex items-center gap-2 rounded-full border border-white/10 px-3.5 py-2 text-sm text-gray-300 transition-colors hover:border-indigo-400/60 hover:text-white">
                <Download className="h-4 w-4" /> Markdown
              </button>
            )}
          </div>
          <div key={tab} className="animate-fade-in p-4 md:p-6">
            {tab === 'review' && <ReviewView result={result} label={label} title={title} />}
            {tab === 'papers' && <PapersView result={result} label={label} />}
            {tab === 'comparison' && <ComparisonView result={result} label={label} title={title} />}
            {tab === 'gaps' && <GapsView result={result} label={label} />}
            {tab === 'evidence' && <EvidenceView result={result} label={label} />}
          </div>
        </GlassCard>
      )}
    </div>
  )
}
