import { AlertTriangle, Loader2, Play, Search, Square } from 'lucide-react'
import { GlassCard } from './ui.jsx'

export default function QueryPanel({ question, setQuestion, examples, maxPapers, setMaxPapers, running, onRun, onStop, error, backendError }) {
  return (
    <GlassCard className="mx-auto max-w-4xl p-3 transition-all duration-300 focus-within:border-indigo-500/50 focus-within:shadow-[0_0_50px_rgba(99,102,241,0.18)]">
      <div className="flex items-start gap-4 px-3 pt-3">
        <Search className="mt-2 h-6 w-6 shrink-0 text-gray-500" />
        <label htmlFor="q" className="sr-only">Research question</label>
        <textarea
          id="q" rows={3} value={question} maxLength={1000} disabled={running}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Enter a research question (e.g. 'Compare how REALM and the original RAG paper integrate retrieval into language models')"
          className="min-h-[5.5rem] w-full resize-none border-none bg-transparent text-lg leading-relaxed text-white outline-none placeholder:text-gray-600 disabled:opacity-60"
        />
      </div>

      <div className="flex flex-wrap items-center gap-2 px-4 pt-2">
        {examples.map((ex) => (
          <button key={ex} type="button" disabled={running} onClick={() => setQuestion(ex)}
            className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-left text-xs text-gray-400 transition-colors hover:border-indigo-400/50 hover:bg-indigo-500/10 hover:text-indigo-200 disabled:opacity-40">
            {ex.length > 58 ? `${ex.slice(0, 56)}…` : ex}
          </button>
        ))}
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-3 border-t border-white/5 px-4 py-3">
        <div className="flex items-center gap-5 text-xs text-gray-400">
          <label className="flex items-center gap-2">
            Max papers to analyse
            <select value={maxPapers} disabled={running} onChange={(e) => setMaxPapers(Number(e.target.value))}
              className="rounded-lg border border-white/10 bg-ink px-2 py-1 text-gray-200">
              {[1, 2, 3, 4, 5, 6].map((n) => <option key={n}>{n}</option>)}
            </select>
          </label>
          <span className="font-mono text-gray-500">{question.length}/1000</span>
        </div>

        {running ? (
          <button onClick={onStop} className="flex h-12 items-center gap-2 rounded-2xl border border-white/10 bg-white/10 px-8 font-medium text-white transition-colors hover:bg-white/15">
            <Loader2 className="h-4 w-4 animate-spin" /> Running… <Square className="h-4 w-4" /> Stop
          </button>
        ) : (
          <button onClick={onRun} disabled={!!backendError}
            className="flex h-12 items-center gap-2 rounded-2xl bg-gradient-to-r from-indigo-600 to-purple-600 px-8 font-semibold text-white shadow-lg shadow-indigo-900/50 transition-all hover:opacity-90 hover:shadow-indigo-700/40 disabled:cursor-not-allowed disabled:opacity-50">
            <Play className="h-4 w-4" /> Run research pipeline
          </button>
        )}
      </div>

      {error && (
        <p className="mx-4 mb-3 flex animate-fade-in items-start gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200" role="alert">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />{error}
        </p>
      )}
    </GlassCard>
  )
}
