import { ArrowRight, BadgeCheck, FileSearch, Quote } from 'lucide-react'
import { GlassCard, Pill, StatusBadge } from './ui.jsx'

const POINTS = [
  { icon: Quote, text: 'Every claim cites a paper, page and passage' },
  { icon: FileSearch, text: 'Quotes are checked against the source text in code' },
  { icon: BadgeCheck, text: 'Unsupported claims are flagged, never hidden' },
]

export default function Hero({ health, papers, backendError, label }) {
  const maxChunks = Math.max(1, ...papers.map((p) => p.chunks || 0))
  const status = backendError
    ? { tone: 'red', text: 'Backend offline' }
    : health
      ? { tone: 'emerald', text: `${health.papers} papers · ${health.chunks} passages indexed` }
      : { tone: 'amber', text: 'Connecting to backend…' }

  return (
    <section id="home" className="relative overflow-hidden px-6 pb-20 pt-32 lg:pb-32 lg:pt-44">
      <div className="pointer-events-none absolute left-1/2 top-0 -z-10 h-[600px] w-[1000px] -translate-x-1/2 animate-glow-pulse rounded-full bg-indigo-600/20 blur-[120px]" />
      <div className="pointer-events-none absolute bottom-0 right-0 -z-10 h-[600px] w-[800px] rounded-full bg-purple-900/20 blur-[100px]" />
      <div className="bg-grid pointer-events-none absolute inset-0 -z-10" />

      <div className="mx-auto grid max-w-7xl items-center gap-12 lg:grid-cols-2">
        <div className="z-10 space-y-8">
          <div className="animate-fade-in-up"><Pill tone={status.tone} className="px-4 py-1.5 text-xs"><span className="h-1.5 w-1.5 rounded-full bg-current" />{status.text}</Pill></div>

          <h1 className="animate-fade-in-up text-5xl font-bold leading-[1.05] tracking-tight text-white [animation-delay:80ms] lg:text-7xl">
            Multi-Agent <br />
            Research <span className="font-serif font-normal italic text-gradient">Intelligence.</span>
          </h1>

          <p className="max-w-lg animate-fade-in-up text-lg leading-relaxed text-gray-400 [animation-delay:160ms]">
            Specialised agents retrieve, read, critique and compare academic papers, then write a literature review in which every claim is traceable to its source and carries a verification status.
          </p>

          <div className="flex animate-fade-in-up flex-wrap gap-4 [animation-delay:240ms]">
            <a href="#workspace" className="group inline-flex items-center gap-2 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 px-8 py-4 font-semibold text-white shadow-lg shadow-indigo-900/50 transition-all hover:opacity-90 hover:shadow-indigo-700/40">
              Start Researching <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </a>
            <a href="#pipeline" className="rounded-full border border-white/10 bg-white/5 px-8 py-4 font-semibold text-white transition-colors hover:bg-white/10">
              How It Works
            </a>
          </div>

          <ul className="animate-fade-in-up space-y-2.5 pt-2 [animation-delay:320ms]">
            {POINTS.map((point) => (
              <li key={point.text} className="flex items-center gap-3 text-sm text-gray-400">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg border border-white/10 bg-white/5"><point.icon className="h-3.5 w-3.5 text-indigo-300" /></span>
                {point.text}
              </li>
            ))}
          </ul>
        </div>

        <div className="relative hidden h-[540px] w-full lg:block">
          <GlassCard className="absolute right-4 top-0 z-20 w-80 animate-float-slow bg-gradient-to-bl from-gray-800/80 to-gray-900/80 p-6">
            <p className="mb-1 text-sm text-gray-400">Citation verification</p>
            <h3 className="mb-5 text-xl font-semibold text-white">Every claim is checked</h3>
            <div className="flex flex-wrap gap-2">
              <StatusBadge status="supported" /><StatusBadge status="partially_supported" />
              <StatusBadge status="unsupported" /><StatusBadge status="unverified" />
            </div>
            <p className="mt-5 text-xs leading-relaxed text-gray-500">Each statement is judged against the exact passage it cites. Flagged claims stay visible.</p>
          </GlassCard>

          <GlassCard className="absolute bottom-0 left-2 z-30 w-80 animate-float-slower border-white/20 bg-white/5 p-6 backdrop-blur-2xl">
            <div className="mb-5 flex items-center justify-between">
              <span className="text-sm text-gray-300">Corpus</span>
              <span className="rounded bg-indigo-500/20 px-2 py-1 text-xs text-indigo-300">passages per paper</span>
            </div>
            <div className="flex h-28 items-end justify-between gap-2">
              {papers.length === 0
                ? [55, 80, 45, 90, 65, 70].map((h, i) => <div key={i} className="skeleton w-full rounded-t-sm" style={{ height: `${h}%` }} />)
                : papers.map((p) => (
                    <div key={p.paper_id} title={`${p.title}: ${p.chunks} passages`} className="w-full rounded-t-sm bg-indigo-500/40 transition-colors hover:bg-indigo-400" style={{ height: `${Math.max(8, ((p.chunks || 0) / maxChunks) * 100)}%` }} />
                  ))}
            </div>
            <div className="mt-3 flex justify-between gap-1 font-mono text-[10px] text-gray-500">
              {papers.map((p) => <span key={p.paper_id} className="w-full truncate text-center">{label(p.paper_id).split(' ')[0].replace(/[^\w-]/g, '')}</span>)}
            </div>
          </GlassCard>
        </div>
      </div>
    </section>
  )
}
