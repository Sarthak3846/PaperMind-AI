import { BadgeCheck, BookOpenText, Bot, FileText, GitCompare, Lightbulb, MessageSquareWarning, ScanText, Search, Workflow } from 'lucide-react'
import { GlassCard, Pill, Reveal, SectionHeading } from './ui.jsx'

const STEPS = [
  { title: 'Understand & Retrieve', icon: Search, prompts: ['P1'], desc: 'The question becomes a retrieval plan; BM25 finds page-aware passages in the selected papers.' },
  { title: 'Extract & Critique', icon: MessageSquareWarning, prompts: ['P2', 'P5'], desc: 'Verbatim evidence is extracted, checked against the source text, then challenged by a critic.' },
  { title: 'Analyse & Compare', icon: GitCompare, prompts: ['P3', 'P4', 'P6'], desc: 'Each paper is analysed alone, then compared, and research gaps are separated into explicit and inferred.' },
  { title: 'Write & Verify', icon: FileText, prompts: ['P7', 'P8'], desc: 'A structured literature review is written, and every claim is verified against its cited passage.' },
]

const AGENTS = [
  { name: 'Search Agent', prompt: 'P1', icon: Search, tone: 'text-blue-300 bg-blue-500/15', desc: 'Interprets the question and plans retrieval.' },
  { name: 'Reader Agent', prompt: 'P2', icon: ScanText, tone: 'text-emerald-300 bg-emerald-500/15', desc: 'Extracts verbatim, citable evidence.' },
  { name: 'Critic Agent', prompt: 'P5', icon: MessageSquareWarning, tone: 'text-red-300 bg-red-500/15', desc: 'Keeps only relevant, well-supported evidence.' },
  { name: 'Paper Analyst', prompt: 'P3', icon: FileText, tone: 'text-cyan-300 bg-cyan-500/15', desc: 'Builds a structured analysis of one paper.' },
  { name: 'Comparison Agent', prompt: 'P4', icon: GitCompare, tone: 'text-pink-300 bg-pink-500/15', desc: 'Compares studies and spots true contradictions.' },
  { name: 'Research Gap Agent', prompt: 'P6', icon: Lightbulb, tone: 'text-orange-300 bg-orange-500/15', desc: 'Finds explicit and inferred research gaps.' },
  { name: 'Teacher Agent', prompt: 'P7', icon: BookOpenText, tone: 'text-fuchsia-300 bg-fuchsia-500/15', desc: 'Writes the cited literature review.' },
  { name: 'Citation Verifier', prompt: 'P8', icon: BadgeCheck, tone: 'text-lime-300 bg-lime-500/15', desc: 'Judges each claim against its source.' },
  { name: 'Root Agent', prompt: null, icon: Workflow, tone: 'text-purple-300 bg-purple-500/15', desc: 'Orchestrates the stages and streams live events.' },
]

export default function PipelineSection() {
  return (
    <>
      <section id="pipeline" className="bg-black/20 px-6 py-24">
        <div className="mx-auto max-w-7xl">
          <SectionHeading title="The Research Pipeline" subtitle="From a research question to a verified literature review, in ten observable stages." />
          <div className="relative grid gap-8 md:grid-cols-4">
            <div className="absolute left-0 top-12 z-0 hidden h-0.5 w-full bg-gradient-to-r from-indigo-500/0 via-indigo-500/50 to-indigo-500/0 md:block" />
            {STEPS.map((s, i) => (
              <Reveal key={s.title} delay={i * 100} className="group relative z-10 flex flex-col items-center text-center">
                <div className="mb-6 flex h-24 w-24 items-center justify-center rounded-2xl border border-white/10 bg-ink shadow-xl transition-all duration-300 group-hover:-translate-y-1 group-hover:border-indigo-500/50 group-hover:shadow-indigo-900/40">
                  <s.icon className="h-8 w-8 text-indigo-400" />
                </div>
                <div className="mb-2 flex items-center gap-2">
                  <span className="font-mono text-xs text-gray-600">0{i + 1}</span>
                  <h3 className="text-lg font-bold text-white">{s.title}</h3>
                </div>
                <p className="mb-3 text-sm leading-relaxed text-gray-400">{s.desc}</p>
                <div className="flex gap-1.5">{s.prompts.map((p) => <Pill key={p} tone="indigo" className="font-mono">{p}</Pill>)}</div>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      <section id="agents" className="relative overflow-hidden px-6 py-24">
        <div className="pointer-events-none absolute left-1/2 top-1/2 -z-10 h-[800px] w-[800px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-indigo-500/5 blur-3xl" />
        <div className="mx-auto max-w-5xl">
          <SectionHeading title="Meet the Agents" subtitle="Eight specialised prompts coordinated by a plain-code Root Agent. A failed stage never feeds its error text to the next agent." />
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {AGENTS.map((a, i) => (
              <Reveal key={a.name} delay={(i % 3) * 80}>
                <GlassCard className="h-full rounded-2xl p-5 transition-colors duration-300 hover:bg-white/[0.08]">
                  <div className="mb-3 flex items-center justify-between">
                    <div className={`rounded-lg p-2 ${a.tone}`}><a.icon className="h-5 w-5" /></div>
                    {a.prompt ? <Pill tone="indigo" className="font-mono">{a.prompt}</Pill> : <Pill tone="purple"><Bot className="h-3 w-3" />code</Pill>}
                  </div>
                  <h4 className="text-sm font-bold text-white">{a.name}</h4>
                  <p className="mt-1 text-xs leading-relaxed text-gray-400">{a.desc}</p>
                </GlassCard>
              </Reveal>
            ))}
          </div>
        </div>
      </section>
    </>
  )
}
