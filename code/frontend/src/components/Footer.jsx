import { Layers } from 'lucide-react'
import { API_BASE } from '../api.js'

export default function Footer() {
  return (
    <footer className="border-t border-white/5 bg-black/20 px-6 py-12">
      <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-6 md:flex-row md:items-center">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600"><Layers className="h-5 w-5 text-white" /></div>
          <div>
            <p className="font-bold text-white">PaperMind<span className="text-indigo-400"> AI</span></p>
            <p className="text-xs text-gray-500">Multi-agent RAG for research intelligence · Team Cognition Labs · SCSE4041</p>
          </div>
        </div>
        <p className="max-w-md text-xs leading-relaxed text-gray-500">
          Answers come only from the indexed PDFs. The system analyses retrieved passages, not whole papers; check every claim against its cited source before use.
          <a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer" className="ml-1 text-indigo-300 hover:underline">API docs</a>
        </p>
      </div>
    </footer>
  )
}
