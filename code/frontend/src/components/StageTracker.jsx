import { AlertTriangle, Check, Loader2, X } from 'lucide-react'
import { STAGES, stageState } from '../stages.js'

const LOOK = {
  pending: 'border-white/10 bg-white/[0.02] text-gray-600',
  running: 'border-indigo-400 bg-indigo-500/20 text-indigo-200 shadow-[0_0_24px_rgba(99,102,241,0.45)]',
  done: 'border-emerald-500/50 bg-emerald-500/15 text-emerald-300',
  warn: 'border-amber-500/50 bg-amber-500/15 text-amber-300',
  error: 'border-red-500/50 bg-red-500/15 text-red-300',
  stopped: 'border-white/15 bg-white/5 text-gray-500',
}

export default function StageTracker({ events, running }) {
  return (
    <ol className="scroll-thin flex gap-1 overflow-x-auto pb-2" aria-label="Pipeline progress">
      {STAGES.map(([id, name, Icon], i) => {
        const st = stageState(events, id, running)
        const Mark = st === 'running' ? Loader2 : st === 'done' ? Check : st === 'warn' ? AlertTriangle : st === 'error' ? X : Icon
        return (
          <li key={id} className="flex min-w-[4.5rem] flex-1 flex-col items-center gap-2" aria-label={`${name}: ${st}`}>
            <div className="flex w-full items-center">
              <span className={`h-px flex-1 ${i === 0 ? 'opacity-0' : st === 'pending' ? 'bg-white/10' : 'bg-indigo-400/50'}`} />
              <span className={`flex h-9 w-9 items-center justify-center rounded-full border transition-all duration-500 ${LOOK[st]}`}>
                <Mark className={`h-4 w-4 ${st === 'running' ? 'animate-spin' : ''}`} />
              </span>
              <span className={`h-px flex-1 ${i === STAGES.length - 1 ? 'opacity-0' : st === 'done' || st === 'warn' ? 'bg-indigo-400/50' : 'bg-white/10'}`} />
            </div>
            <span className={`text-[11px] font-medium ${st === 'pending' ? 'text-gray-600' : 'text-gray-300'}`}>{name}</span>
          </li>
        )
      })}
    </ol>
  )
}
