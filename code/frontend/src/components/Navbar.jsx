import { useEffect, useState } from 'react'
import { Layers } from 'lucide-react'

export default function Navbar({ health, backendError }) {
  const [scrolled, setScrolled] = useState(false)
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  const online = !!health && !backendError
  const dot = backendError ? 'bg-red-500' : online ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'
  const text = backendError ? 'Backend offline' : online ? 'Backend online' : 'Connecting…'

  return (
    <nav className={`fixed inset-x-0 top-0 z-50 px-6 transition-all duration-300 ${scrolled ? 'border-b border-white/5 bg-ink/75 py-3 backdrop-blur-xl' : 'py-5'}`}>
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <a href="#home" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-900/50">
            <Layers className="h-5 w-5 text-white" />
          </div>
          <span className="text-xl font-bold tracking-tight text-white">PaperMind<span className="text-indigo-400"> AI</span></span>
        </a>

        <div className={`hidden items-center gap-8 rounded-full border px-8 py-3 backdrop-blur-md transition-colors duration-300 md:flex ${scrolled ? 'border-white/10 bg-black/50' : 'border-white/5 bg-black/20'}`}>
          <a href="#home" className="text-sm font-medium text-white transition-colors hover:text-indigo-300">Home</a>
          <a href="#pipeline" className="text-sm font-medium text-gray-400 transition-colors hover:text-white">How It Works</a>
          <a href="#agents" className="text-sm font-medium text-gray-400 transition-colors hover:text-white">Agents</a>
          <a href="#workspace" className="text-sm font-medium text-gray-400 transition-colors hover:text-white">Workspace</a>
        </div>

        <div className="flex items-center gap-3">
          <span className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-gray-300 lg:inline-flex" role="status">
            <span className={`h-2 w-2 rounded-full ${dot}`} />{text}
          </span>
          <a href="#workspace" className="rounded-full bg-white px-6 py-2.5 text-sm font-bold text-black transition-colors hover:bg-gray-200">
            Open Workspace
          </a>
        </div>
      </div>
    </nav>
  )
}
