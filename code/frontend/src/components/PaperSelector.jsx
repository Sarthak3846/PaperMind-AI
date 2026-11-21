import { BookOpen, Check } from 'lucide-react'
import { GlassCard } from './ui.jsx'

export default function PaperSelector({ papers, selected, onToggle, onClear, running }) {
  return (
    <GlassCard className="rounded-2xl p-5 lg:sticky lg:top-24">
      <div className="mb-1 flex items-center justify-between">
        <h2 className="flex items-center gap-2 font-semibold text-white"><BookOpen className="h-4 w-4 text-indigo-300" /> Paper selection</h2>
        <button type="button" disabled={running || selected.size === 0} onClick={onClear} className="text-xs text-indigo-300 transition-colors hover:text-indigo-200 disabled:text-gray-600">search all</button>
      </div>
      <p className="mb-4 text-xs text-gray-500">{selected.size ? `${selected.size} selected: only these are searched.` : 'None selected: all papers are searched.'}</p>

      <ul className="scroll-thin max-h-[26rem] space-y-2 overflow-y-auto pr-1">
        {papers.length === 0 && [1, 2, 3, 4].map((i) => <li key={i} className="skeleton h-16 rounded-xl" />)}
        {papers.map((p) => {
          const on = selected.has(p.paper_id)
          return (
            <li key={p.paper_id}>
              <label className={`flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition-all duration-200 ${on ? 'border-indigo-400/60 bg-indigo-500/10' : 'border-white/5 bg-white/[0.02] hover:border-white/15 hover:bg-white/[0.05]'} ${running ? 'pointer-events-none opacity-60' : ''}`}>
                <input type="checkbox" className="peer sr-only" checked={on} disabled={running} onChange={() => onToggle(p.paper_id)} />
                <span className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border transition-colors peer-focus-visible:ring-2 peer-focus-visible:ring-indigo-400 ${on ? 'border-indigo-400 bg-indigo-500' : 'border-white/20 bg-transparent'}`}>
                  {on && <Check className="h-3.5 w-3.5 text-white" />}
                </span>
                <span className="min-w-0 text-xs">
                  <span className="block font-medium leading-snug text-gray-100">{p.title}</span>
                  <span className="mt-1 block text-gray-500">{p.authors || 'authors n/a'}{p.year ? `, ${p.year}` : ''} · {p.pages} pages · {p.chunks} passages</span>
                </span>
              </label>
            </li>
          )
        })}
      </ul>
    </GlassCard>
  )
}
