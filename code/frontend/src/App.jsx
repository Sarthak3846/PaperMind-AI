import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { Bot, Loader2 } from 'lucide-react'
import { API_BASE, fetchHealth, fetchPapers, streamResearch } from './api.js'
import { reviewToMarkdown } from './export.js'
import Navbar from './components/Navbar.jsx'
import Hero from './components/Hero.jsx'
import PipelineSection from './components/PipelineSection.jsx'
import QueryPanel from './components/QueryPanel.jsx'
import PaperSelector from './components/PaperSelector.jsx'
import StageTracker from './components/StageTracker.jsx'
import ExecutionLog from './components/ExecutionLog.jsx'
import ResultPanel from './components/ResultPanel.jsx'
import Footer from './components/Footer.jsx'
import { GlassCard, Pill, SectionHeading } from './components/ui.jsx'

const EXAMPLES = [
  'What problem does Self-RAG address and how does it work?',
  'Compare how REALM and the original RAG paper integrate retrieval into language models',
  'What research gaps exist in evaluating retrieval-augmented generation?',
  'Do the papers agree on when a model should retrieve?',
]

export default function App() {
  const [papers, setPapers] = useState([])
  const [health, setHealth] = useState(null)
  const [backendError, setBackendError] = useState('')
  const [question, setQuestion] = useState('')
  const [selected, setSelected] = useState(new Set())
  const [maxPapers, setMaxPapers] = useState(4)
  const [events, setEvents] = useState([])
  const [result, setResult] = useState(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState('')
  const [tab, setTab] = useState('review')
  const abortRef = useRef(null)
  const progressRef = useRef(null)

  useEffect(() => {
    Promise.all([fetchPapers(), fetchHealth()])
      .then(([p, h]) => { setPapers(p.papers); setHealth(h) })
      .catch((e) => setBackendError(`Cannot reach the backend at ${API_BASE}: ${e.message}`))
  }, [])

  const byId = useMemo(() => Object.fromEntries(papers.map((p) => [p.paper_id, p])), [papers])
  const label = useCallback((id) => {
    const p = byId[id]
    if (!p) return id
    return p.authors ? `${p.authors.replace(' et al.', '')}${p.year ? ` ${p.year}` : ''}` : p.title.split(' ').slice(0, 3).join(' ')
  }, [byId])
  const title = useCallback((id) => byId[id]?.title || id, [byId])

  const toggle = (id) => setSelected((s) => { const n = new Set(s); if (n.has(id)) n.delete(id); else n.add(id); return n })

  async function run() {
    setError(''); setResult(null); setEvents([]); setTab('review')
    if (!question.trim()) { setError('Please enter a research question.'); return }
    const ctrl = new AbortController()
    abortRef.current = ctrl
    setRunning(true)
    requestAnimationFrame(() => progressRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
    try {
      await streamResearch(
        { question: question.trim(), paper_ids: selected.size ? [...selected] : null, max_papers: maxPapers },
        (ev) => {
          if (ev.type === 'result') setResult(ev.data.result)
          setEvents((prev) => [...prev, ev])
        },
        ctrl.signal,
      )
    } catch (e) {
      if (e.name !== 'AbortError') setError(e.message)
    } finally {
      setRunning(false)
      abortRef.current = null
    }
  }

  const stop = () => abortRef.current?.abort()

  function download() {
    const md = reviewToMarkdown(result, title)
    const url = URL.createObjectURL(new Blob([md], { type: 'text/markdown' }))
    const a = Object.assign(document.createElement('a'), { href: url, download: 'papermind-literature-review.md' })
    a.click()
    URL.revokeObjectURL(url)
  }

  const started = events.length > 0 || running

  return (
    <div className="min-h-screen bg-ink font-sans text-white selection:bg-indigo-500/30">
      <Navbar health={health} backendError={backendError} />
      <Hero health={health} papers={papers} backendError={backendError} label={label} />
      <PipelineSection />

      <section id="workspace" className="relative px-6 py-24">
        <div className="pointer-events-none absolute right-0 top-20 -z-10 h-[500px] w-[700px] rounded-full bg-purple-900/10 blur-[110px]" />
        <div className="mx-auto max-w-7xl">
          <SectionHeading title="Interactive Research Workspace" subtitle="Ask a question, choose the papers to search, and watch the agents work in real time.">
            {health && (
              <div className="mt-5 flex flex-wrap items-center justify-center gap-2">
                <Pill>{health.papers} papers · {health.chunks} passages</Pill>
                <Pill>model: {health.model}</Pill>
                <Pill>prompts: {health.prompt_version}</Pill>
                {!health.gemini_configured && <Pill tone="red">GEMINI_API_KEY not set</Pill>}
              </div>
            )}
          </SectionHeading>

          {backendError && (
            <GlassCard className="mx-auto mb-6 max-w-4xl border-red-500/40 bg-red-500/[0.06] p-5" >
              <p className="text-sm text-red-200" role="alert">{backendError}</p>
              <p className="mt-1 text-xs text-gray-500">Start the backend (see README), then reload this page.</p>
            </GlassCard>
          )}

          <QueryPanel
            question={question} setQuestion={setQuestion} examples={EXAMPLES}
            maxPapers={maxPapers} setMaxPapers={setMaxPapers} running={running}
            onRun={run} onStop={stop} error={error} backendError={backendError}
          />

          <div className="mt-10 grid gap-6 lg:grid-cols-[340px_1fr]">
            <PaperSelector papers={papers} selected={selected} onToggle={toggle} onClear={() => setSelected(new Set())} running={running} />

            <div ref={progressRef} className="min-w-0 space-y-5">
              <GlassCard className="rounded-2xl p-5">
                <div className="mb-4 flex flex-wrap items-center justify-between gap-x-4 gap-y-1">
                  <h2 className="text-sm font-semibold text-white">Live agent execution</h2>
                  <span className="text-[11px] text-gray-500">events streamed from the backend</span>
                </div>
                {started && <div className="mb-4"><StageTracker events={events} running={running} /></div>}
                <ExecutionLog events={events} running={running} />
                <p className="mt-3 text-xs text-gray-600">Every line above is an event emitted by the server while that stage was executing. Nothing is simulated.</p>
              </GlassCard>

              {result && (
                <ResultPanel result={result} tab={tab} onTab={setTab} label={label} title={title} onDownload={download} />
              )}

              {!result && !running && (
                <GlassCard className="rounded-2xl p-10 opacity-60">
                  <div className="flex flex-col items-center gap-3 text-center text-gray-500">
                    <Bot className="h-12 w-12 opacity-30" />
                    <p className="text-sm">Your literature review, paper analyses, comparison and research gaps will appear here.</p>
                  </div>
                </GlassCard>
              )}

              {running && !result && (
                <GlassCard className="rounded-2xl p-6">
                  <div className="mb-4 flex items-center gap-2 text-xs text-gray-400">
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-indigo-400" />
                    A full run makes roughly 8–16 model calls and can take 1–2 minutes.
                  </div>
                  <div className="space-y-3">
                    <div className="skeleton h-4 w-2/3 rounded" /><div className="skeleton h-4 w-full rounded" /><div className="skeleton h-4 w-5/6 rounded" />
                  </div>
                </GlassCard>
              )}
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  )
}
