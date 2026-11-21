import { BadgeCheck, BookOpenText, Database, FileText, GitCompare, Lightbulb, MessageSquareWarning, ScanText, Search, ShieldCheck } from 'lucide-react'

export const STAGES = [
  ['validate_input', 'Validate', ShieldCheck], ['query_understanding', 'Understand', Search],
  ['retrieval', 'Retrieve', Database], ['evidence_extraction', 'Extract', ScanText],
  ['evidence_critique', 'Critique', MessageSquareWarning], ['paper_analysis', 'Analyse', FileText],
  ['comparison', 'Compare', GitCompare], ['gap_identification', 'Gaps', Lightbulb],
  ['literature_review', 'Review', BookOpenText], ['citation_verification', 'Verify', BadgeCheck],
]

/** State of one stage, derived ONLY from the events the backend has streamed so far. */
export function stageState(events, stage, running) {
  const evs = events.filter((e) => e.stage === stage)
  if (!evs.length) return 'pending'
  if (evs.some((e) => e.type === 'stage_error')) return 'error'
  const key = (e) => e.data?.paper_id || ''
  const ended = new Set(evs.filter((e) => e.type === 'stage_done' || e.type === 'stage_warning').map(key))
  const open = evs.some((e) => e.type === 'stage_start' && !ended.has(key(e)))
  if (open) return running ? 'running' : 'stopped'
  return evs.some((e) => e.type === 'stage_done') ? 'done' : 'warn'
}
