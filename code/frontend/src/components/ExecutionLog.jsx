import { useEffect, useRef } from 'react'
import { Terminal } from 'lucide-react'
import { Pill } from './ui.jsx'

const AGENT_COLOR = {
  RootAgent: 'text-purple-400', SearchAgent: 'text-blue-400', Retriever: 'text-yellow-400',
  ReaderAgent: 'text-emerald-400', CriticAgent: 'text-red-400', PaperAnalystAgent: 'text-cyan-400',
  ComparisonAgent: 'text-pink-400', ResearchGapAgent: 'text-orange-400', TeacherAgent: 'text-fuchsia-400',
  CitationVerifier: 'text-lime-400',
}

const MARK = {
  stage_start: ['▸', 'text-gray-500'], stage_progress: ['…', 'text-gray-500'], stage_done: ['✓', 'text-emerald-400'],
  stage_warning: ['!', 'text-amber-400'], stage_error: ['✕', 'text-red-400'],
}

function clock(ts) {
  const d = new Date(ts)
  return Number.isNaN(d.getTime()) ? '--:--:--' : d.toLocaleTimeString('en-GB', { hour12: false })
}

/** Terminal-style log. Every line is an event streamed by the backend while that stage was running. */
export default function ExecutionLog({ events, running }) {
  const scrollRef = useRef(null)
  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
  }, [events, running])

  return (
    <div className="w-full overflow-hidden rounded-2xl border border-white/10 bg-[#0F0F1A] font-mono text-sm shadow-2xl">
      <div className="flex items-center justify-between gap-3 border-b border-white/5 bg-white/5 px-4 py-2">
        <div className="flex min-w-0 items-center gap-2">
          <div className="flex shrink-0 gap-1.5">
            <span className="h-3 w-3 rounded-full bg-red-500/80" /><span className="h-3 w-3 rounded-full bg-yellow-500/80" /><span className="h-3 w-3 rounded-full bg-green-500/80" />
          </div>
          <span className="ml-2 flex min-w-0 items-center gap-2 truncate text-xs text-gray-500"><Terminal className="h-3 w-3 shrink-0" /><span className="truncate">agent_pipeline: live execution log</span></span>
        </div>
        <span className={`shrink-0 text-xs ${running ? 'animate-pulse text-emerald-400' : 'text-gray-600'}`}>{running ? '● Live execution' : `${events.length} events`}</span>
      </div>

      <div ref={scrollRef} className="scroll-thin h-[320px] space-y-1.5 overflow-y-auto p-5" role="log" aria-live="polite">
        {events.length === 0 && !running && <div className="italic text-gray-600">Waiting for query execution command...</div>}
        {events.length === 0 && running && <div className="text-gray-500">Connecting to the backend…</div>}
        {events.map((e, i) => {
          const isResult = e.type === 'result'
          const status = e.data?.result?.status
          const [mark, markColor] = isResult
            ? (status === 'completed' ? ['■', 'text-emerald-400'] : status === 'insufficient_evidence' ? ['■', 'text-amber-400'] : ['■', 'text-red-400'])
            : (MARK[e.type] || ['·', 'text-gray-500'])
          const dim = e.type === 'stage_start' || e.type === 'stage_progress'
          return (
            <div key={`${e.seq}-${i}`} className="flex animate-slide-in gap-3 leading-relaxed">
              <span className="select-none text-gray-600">{clock(e.ts)}</span>
              <span className={`select-none ${markColor}`}>{mark}</span>
              <div className="min-w-0 flex-1">
                <span className={`mr-2 font-bold ${AGENT_COLOR[e.agent] || 'text-gray-300'}`}>[{e.agent}]</span>
                {e.prompt && <Pill tone="indigo" className="mr-2 px-1.5 py-0 font-mono text-[10px]">{e.prompt}</Pill>}
                <span className={dim ? 'text-gray-500' : e.type === 'stage_error' ? 'text-red-300' : e.type === 'stage_warning' ? 'text-amber-200' : 'text-gray-300'}>{e.message}</span>
                {e.duration_ms != null && <span className="ml-2 text-xs text-gray-600">{(e.duration_ms / 1000).toFixed(1)}s</span>}
              </div>
            </div>
          )
        })}
        {running && (
          <div className="flex gap-3">
            <span className="select-none text-transparent">00:00:00</span>
            <span className="h-4 w-2 animate-blink bg-gray-500" />
          </div>
        )}
      </div>
    </div>
  )
}
