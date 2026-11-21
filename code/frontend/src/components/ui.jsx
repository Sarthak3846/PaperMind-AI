import { useEffect, useRef, useState } from 'react'
import { AlertTriangle, CheckCircle2, HelpCircle, XCircle, FileText } from 'lucide-react'

/** Frosted-glass surface (the signature element of the original DebateRAG design). */
export function GlassCard({ children, className = '' }) {
  return (
    <div className={`relative overflow-hidden rounded-3xl border border-white/10 bg-white/[0.04] shadow-2xl shadow-black/30 backdrop-blur-xl ${className}`}>
      {children}
    </div>
  )
}

/** Smaller surface for content blocks inside result views. */
export function Card({ children, className = '' }) {
  return <div className={`rounded-2xl border border-white/10 bg-white/[0.03] p-5 ${className}`}>{children}</div>
}

const TONES = {
  slate: 'bg-white/5 text-gray-300 border-white/10',
  indigo: 'bg-indigo-500/15 text-indigo-300 border-indigo-500/30',
  purple: 'bg-purple-500/15 text-purple-300 border-purple-500/30',
  amber: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  emerald: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  red: 'bg-red-500/15 text-red-300 border-red-500/30',
}

export function Pill({ children, tone = 'slate', className = '' }) {
  return (
    <span className={`inline-flex items-center gap-1 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${TONES[tone] || TONES.slate} ${className}`}>
      {children}
    </span>
  )
}

const STATUS = {
  supported: { label: 'Supported', tone: 'emerald', Icon: CheckCircle2 },
  partially_supported: { label: 'Partially supported', tone: 'amber', Icon: AlertTriangle },
  unsupported: { label: 'Unsupported', tone: 'red', Icon: XCircle },
  unverified: { label: 'Unverified', tone: 'slate', Icon: HelpCircle },
}

export function StatusBadge({ status, reason }) {
  const s = STATUS[status]
  if (!s) return null
  return (
    <span title={reason || s.label}>
      <Pill tone={s.tone}><s.Icon size={12} />{s.label}</Pill>
    </span>
  )
}

export function SectionHeading({ title, subtitle, children }) {
  return (
    <div className="mb-12 text-center">
      <h2 className="mb-4 text-3xl font-bold tracking-tight text-white md:text-4xl">{title}</h2>
      {subtitle && <p className="mx-auto max-w-2xl text-gray-400">{subtitle}</p>}
      {children}
    </div>
  )
}

/** Small-caps title with a fading rule, used inside result tabs. */
export function SectionTitle({ children, hint, className = '' }) {
  return (
    <div className={`mb-3 ${className}`}>
      <div className="flex items-center gap-3">
        <h3 className="text-[11px] font-semibold uppercase tracking-[0.18em] text-indigo-300">{children}</h3>
        <span className="h-px flex-1 bg-gradient-to-r from-indigo-500/30 to-transparent" />
      </div>
      {hint && <p className="mt-1 text-xs text-gray-500">{hint}</p>}
    </div>
  )
}

/** Fades content in when it scrolls into view. */
export function Reveal({ children, className = '', delay = 0 }) {
  const ref = useRef(null)
  const [shown, setShown] = useState(() => typeof IntersectionObserver === 'undefined')
  useEffect(() => {
    const el = ref.current
    if (!el || typeof IntersectionObserver === 'undefined') return undefined
    const io = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) { setShown(true); io.disconnect() }
    }, { threshold: 0.12 })
    io.observe(el)
    return () => io.disconnect()
  }, [])
  return (
    <div
      ref={ref}
      style={{ transitionDelay: `${delay}ms` }}
      className={`transition-all duration-700 ease-out ${shown ? 'translate-y-0 opacity-100' : 'translate-y-6 opacity-0'} ${className}`}
    >
      {children}
    </div>
  )
}

/** Citation chips: paper label + page. Click to read the exact source passage. */
export function Citations({ ids = [], sources, label }) {
  const [open, setOpen] = useState(null)
  if (!ids.length) return null
  return (
    <span className="ml-1 inline-flex flex-wrap items-center gap-1 align-middle">
      {ids.map((id) => {
        const src = sources?.[id]
        const active = open === id
        return (
          <button
            key={id}
            type="button"
            onClick={() => setOpen(active ? null : id)}
            title={src ? `${src.title} - page ${src.page}` : id}
            className={`inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 font-mono text-[11px] transition-colors ${
              active ? 'border-indigo-400 bg-indigo-500/25 text-indigo-100' : 'border-indigo-500/25 bg-indigo-500/10 text-indigo-300 hover:border-indigo-400/60 hover:bg-indigo-500/20'
            }`}
          >
            <FileText size={10} /> {src ? `${label(src.paper_id)} p.${src.page}` : id}
          </button>
        )
      })}
      {open && sources?.[open] && (
        <span className="mt-2 block w-full animate-fade-in rounded-xl border border-white/10 border-l-2 border-l-indigo-400 bg-black/30 p-3 text-xs leading-relaxed text-gray-300">
          <span className="mb-1 block font-mono text-[10px] text-gray-500">{sources[open].chunk_id} · {sources[open].filename}</span>
          {sources[open].text}
        </span>
      )}
    </span>
  )
}
