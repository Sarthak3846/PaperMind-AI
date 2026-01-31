import { useState, useEffect, useRef } from 'react';
import { 
  Search, 
  Database, 
  Filter, 
  MessageSquareWarning, 
  Cpu, 
  FileText, 
  ChevronRight, 
  Activity, 
  Layers, 
  ArrowRight,
  CheckCircle2,
  Bot,
  GitBranch,
  ScanText,
  ShieldCheck,
  BrainCircuit,
  ArrowDown,
  Loader2,
  Terminal, // Added Terminal Icon
  Code2
} from 'lucide-react';

/**
 * Shared UI Components
 */
const GlassCard = ({ children, className = "" }) => (
  <div className={`relative overflow-hidden bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl ${className}`}>
    {children}
  </div>
);

const Badge = ({ children, color = "blue" }) => {
  const colors = {
    blue: "bg-blue-500/20 text-blue-300 border-blue-500/30",
    purple: "bg-purple-500/20 text-purple-300 border-purple-500/30",
    emerald: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
    orange: "bg-orange-500/20 text-orange-300 border-orange-500/30",
  };
  return (
    <span className={`px-3 py-1 rounded-full text-xs font-medium border ${colors[color] || colors.blue}`}>
      {children}
    </span>
  );
};

const SectionHeading = ({ title, subtitle }) => (
  <div className="text-center mb-16">
    <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">{title}</h2>
    <p className="text-gray-400 max-w-2xl mx-auto">{subtitle}</p>
  </div>
);

/**
 * Terminal Window Component
 * Renders the live execution logs with a typing effect
 */
const TerminalWindow = ({ logs }) => {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="w-full font-mono text-sm rounded-2xl overflow-hidden border border-white/10 bg-[#0F0F1A] shadow-2xl">
      {/* Terminal Header */}
      <div className="bg-white/5 px-4 py-2 flex items-center gap-2 border-b border-white/5">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500/80" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
          <div className="w-3 h-3 rounded-full bg-green-500/80" />
        </div>
        <div className="ml-2 flex items-center gap-2 text-xs text-gray-500">
          <Terminal className="w-3 h-3" />
          <span>agent_pipeline.py — Execution Log</span>
        </div>
      </div>
      
      {/* Terminal Body */}
      <div 
        ref={scrollRef}
        className="p-6 h-[300px] overflow-y-auto space-y-2 scroll-smooth"
      >
        {logs.length === 0 && (
          <div className="text-gray-600 italic">Waiting for query execution command...</div>
        )}
        {logs.map((log, idx) => (
          <div key={idx} className="flex gap-3 animate-in fade-in slide-in-from-left-2 duration-300">
            <span className="text-gray-600 select-none">
              {new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' })}
            </span>
            <div>
              <span className={`font-bold mr-2 ${log.color || 'text-blue-400'}`}>[{log.agent}]</span>
              <span className="text-gray-300">{log.message}</span>
            </div>
          </div>
        ))}
        {/* Blinking Cursor */}
        <div className="flex gap-3">
             <span className="text-transparent select-none">00:00:00</span>
             <span className="w-2 h-4 bg-gray-500 animate-pulse" />
        </div>
      </div>
    </div>
  );
};

// ... (Navbar, Hero, PipelineSection, ArchitectureSection, Footer remain mostly the same, 
//      but I will include the full App structure below for easy copy-pasting)

const Navbar = () => (
  <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-6 transition-all duration-300">
    <div className="max-w-7xl mx-auto flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
          <Layers className="w-5 h-5 text-white" />
        </div>
        <span className="text-xl font-bold tracking-tight text-white">DebateRAG<span className="text-indigo-400">.ai</span></span>
      </div>
      
      <div className="hidden md:flex items-center gap-8 bg-black/20 backdrop-blur-md px-8 py-3 rounded-full border border-white/5">
        <a href="#home" className="text-sm font-medium text-white hover:text-indigo-300 transition-colors">Home</a>
        <a href="#pipeline" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">How It Works</a>
        <a href="#architecture" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Architecture</a>
        <a href="#demo" className="text-sm font-medium text-gray-400 hover:text-white transition-colors">Demo</a>
      </div>

      <button className="hidden md:flex bg-white text-black px-6 py-2.5 rounded-full text-sm font-bold hover:bg-gray-200 transition-colors">
        Run Demo
      </button>
    </div>
  </nav>
);

const Hero = () => (
  <section id="home" className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 px-6 overflow-hidden">
    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[600px] bg-indigo-600/20 rounded-full blur-[120px] -z-10" />
    <div className="absolute bottom-0 right-0 w-[800px] h-[600px] bg-purple-900/10 rounded-full blur-[100px] -z-10" />

    <div className="max-w-7xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
      <div className="space-y-8 z-10">
        <div className="flex items-center gap-[-10px]">
           <div className="flex -space-x-3">
             {[1,2,3].map(i => (
               <div key={i} className="w-10 h-10 rounded-full border-2 border-[#0B0B15] bg-gray-700 flex items-center justify-center">
                 <Cpu className="w-5 h-5 text-gray-300" />
               </div>
             ))}
           </div>
           <span className="ml-4 text-sm text-gray-400 font-medium">3 Active Agents Online</span>
        </div>

        <h1 className="text-5xl lg:text-7xl font-bold text-white leading-[1.1]">
          Multi-Agent <br />
          Research <span className="font-serif italic text-indigo-400 font-light">Debate.</span>
        </h1>
        
        <p className="text-lg text-gray-400 max-w-lg leading-relaxed">
          An experimental system where specialized retrieval agents debate, critique, and synthesize evidence across academic documents to reduce hallucinations.
        </p>

        <div className="flex flex-wrap gap-4">
          <a href="#demo" className="px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-full text-white font-semibold hover:opacity-90 transition-opacity shadow-lg shadow-indigo-900/50">
            Try a Query
          </a>
          <button className="px-8 py-4 bg-white/5 border border-white/10 rounded-full text-white font-semibold hover:bg-white/10 transition-colors">
            View Architecture
          </button>
        </div>
      </div>

      <div className="relative h-[500px] w-full hidden lg:block perspective-1000">
        {/* Card 1: Main Evidence Card */}
        <GlassCard className="absolute top-10 right-10 w-80 p-6 z-20 animate-float-slow bg-gradient-to-bl from-gray-800/80 to-gray-900/80">
          <div className="flex justify-between items-start mb-8">
            <div>
              <p className="text-gray-400 text-sm mb-1">Retrieval Status</p>
              <h3 className="text-white text-xl font-semibold">Active Debate</h3>
            </div>
            <Activity className="text-emerald-400 w-6 h-6" />
          </div>
          <div className="space-y-3">
              <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                <div className="h-full w-3/4 bg-emerald-500 rounded-full"></div>
              </div>
              <div className="flex justify-between text-xs text-gray-400">
                <span>Confidence</span>
                <span>88.4%</span>
              </div>
          </div>
          <div className="mt-6 flex justify-between items-center">
            <div className="flex gap-2">
               <span className="w-3 h-3 rounded-full bg-red-500"></span>
               <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
               <span className="w-3 h-3 rounded-full bg-green-500"></span>
            </div>
            <Cpu className="text-gray-500 w-8 h-8" />
          </div>
        </GlassCard>

        {/* Card 2: Chart Card */}
        <GlassCard className="absolute bottom-20 left-10 w-72 p-6 z-30 backdrop-blur-2xl bg-white/5 border-white/20">
          <div className="flex justify-between items-center mb-6">
            <span className="text-sm text-gray-300">Evidence Density</span>
            <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2 py-1 rounded">This Query</span>
          </div>
          <div className="flex items-end justify-between h-32 gap-2">
              {[40, 70, 45, 90, 60, 80].map((h, i) => (
                <div key={i} className="w-full bg-indigo-500/30 rounded-t-sm hover:bg-indigo-400 transition-colors" style={{ height: `${h}%` }}></div>
              ))}
          </div>
          <div className="flex justify-between mt-4 text-xs text-gray-500 font-mono">
            <span>R1</span><span>R2</span><span>R3</span><span>C1</span><span>C2</span><span>FN</span>
          </div>
        </GlassCard>
      </div>
    </div>
  </section>
);

/**
 * Demo Interface
 */
const DemoInterface = () => {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);

  // --- LOGIC: Simulator for the Terminal ---
  const simulateExecution = (userQuery) => {
    const steps = [
      { agent: "Manager", message: `Received Query: "${userQuery}"`, color: "text-purple-400" },
      { agent: "SearchAgent", message: "Delegating to Recall Specialist...", color: "text-blue-400" },
      { agent: "Recall", message: "Fetching raw context from Vector DB...", color: "text-yellow-400" },
      { agent: "Precision", message: "Extracting candidate facts...", color: "text-emerald-400" },
      // --- NEW STEPS ---
      { agent: "Critic", message: "REVIEWING FACTS FOR HALLUCINATIONS...", color: "text-red-400 font-bold" },
      { agent: "Critic", message: "Cross-referencing sources for contradictions...", color: "text-red-400" },
      { agent: "Critic", message: "Debate complete. Validating evidence.", color: "text-red-400" },
      // ----------------
      { agent: "Teacher", message: "Synthesizing Final Verdict...", color: "text-purple-400" },
      { agent: "System", message: "Response Ready.", color: "text-white" }
    ];

    let delay = 0;
    steps.forEach((step, index) => {
      // Stagger the logs to look like real processing
      delay += Math.random() * 800 + 400; // Random delay between 400ms and 1200ms
      setTimeout(() => {
        setLogs(prev => [...prev, step]);
      }, delay);
    });
  };

  const handleSearch = async () => {
    if (!query) return;
    setLoading(true);
    setResult("");
    setLogs([]);
    
    // 1. Start Visual Simulation
    simulateExecution(query);

    try {
      // 2. Real Backend Call
      // NEW (Direct link to Render)
        const response = await fetch('https://debaterag-ai.onrender.com/api/research', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query })
      });
      const data = await response.json();
      
      if (data.status === 'success') {
        // Wait a bit for the animation to catch up if response is too fast
        setTimeout(() => {
            setResult(data.answer);
            setLoading(false);
        }, 5000); // Ensures the user sees the logs before result pops in
      } else {
        setResult("Error: " + data.detail);
        setLoading(false);
      }
    } catch (e) {
      setTimeout(() => {
          setResult("Error: Could not connect to Python backend.");
          setLoading(false);
      }, 3000);
    }
  };

  return (
    <section id="demo" className="py-20 px-6">
      <div className="max-w-7xl mx-auto">
        <SectionHeading 
          title="Interactive Research Environment" 
          subtitle="Watch specialized agents retrieve, filter, and debate evidence in real-time."
        />

        <div className="space-y-8">
          
          {/* 1. QUERY INPUT */}
          <GlassCard className="p-2 flex items-center gap-4 max-w-3xl mx-auto">
              <div className="pl-6 text-gray-400">
                <Search className="w-6 h-6" />
              </div>
              <input 
                type="text" 
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter a complex research question (e.g., 'Impact of transformers on RL efficiency')" 
                className="w-full bg-transparent border-none outline-none text-white h-14 text-lg placeholder:text-gray-600"
              />
              <button 
                onClick={handleSearch}
                disabled={loading}
                className="h-12 px-8 bg-indigo-600 hover:bg-indigo-700 text-white font-medium rounded-2xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {loading ? (
                  <>Running Pipeline <Loader2 className="w-4 h-4 animate-spin" /></>
                ) : (
                  "Run Multi-Agent Retrieval"
                )}
              </button>
          </GlassCard>

          {/* 2. PROCESS VISUALIZATION (TERMINAL & RESULT) */}
          <div className="grid lg:grid-cols-2 gap-8">
             
             {/* Left: The Live Terminal */}
             <div className="space-y-4">
                 <div className="flex items-center justify-between px-2">
                    <h3 className="text-white font-semibold flex items-center gap-2">
                        <Code2 className="w-4 h-4 text-gray-400" /> Pipeline Logs
                    </h3>
                    {loading && <span className="text-xs text-emerald-400 animate-pulse">● Live Execution</span>}
                 </div>
                 <TerminalWindow logs={logs} />
             </div>

             {/* Right: The Final Answer (Moves up here) */}
             <div className="space-y-4">
                 <div className="flex items-center justify-between px-2">
                    <h3 className="text-white font-semibold flex items-center gap-2">
                        <FileText className="w-4 h-4 text-gray-400" /> Synthesized Result
                    </h3>
                 </div>
                 <GlassCard className={`h-[340px] p-8 overflow-y-auto transition-all duration-500 ${result ? 'opacity-100' : 'opacity-50'}`}>
                    {result ? (
                        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4">
                            <div className="flex items-center gap-2 text-emerald-400 mb-2">
                                <CheckCircle2 className="w-5 h-5" />
                                <span className="text-sm font-bold uppercase tracking-wider">Verified Answer</span>
                            </div>
                            <div className="text-gray-200 leading-relaxed whitespace-pre-wrap">
                                {result}
                            </div>
                            <div className="pt-4 border-t border-white/5 flex gap-2">
                                <Badge color="blue">Self-RAG</Badge>
                                <Badge color="purple">Grounded</Badge>
                            </div>
                        </div>
                    ) : (
                        <div className="h-full flex flex-col items-center justify-center text-gray-500 gap-4">
                            {loading ? (
                                <>
                                    <Loader2 className="w-8 h-8 animate-spin text-indigo-500" />
                                    <p className="text-sm">Agents are debating...</p>
                                </>
                            ) : (
                                <>
                                    <Bot className="w-12 h-12 opacity-20" />
                                    <p>Ready to synthesize.</p>
                                </>
                            )}
                        </div>
                    )}
                 </GlassCard>
             </div>
          </div>

          {/* 3. AGENT DETAILS (Bottom Grid) */}
          <div className="pt-10 border-t border-white/5">
            <h3 className="text-gray-400 text-sm font-mono uppercase tracking-widest mb-6 text-center">Agent Architecture Details</h3>
            <div className="grid md:grid-cols-3 gap-6 h-[300px]">
                {/* Recall Agent */}
                <div className="flex flex-col gap-4 opacity-75 hover:opacity-100 transition-opacity">
                    <div className="flex items-center gap-2 mb-2">
                        <Database className="w-5 h-5 text-blue-400" />
                        <h3 className="text-white font-semibold">Recall Agent</h3>
                    </div>
                    <GlassCard className="flex-1 p-5 overflow-y-auto space-y-4 no-scrollbar">
                        {[1,2,3].map((i) => (
                        <div key={i} className="p-3 rounded-xl bg-white/5 border border-white/5">
                            <div className="flex justify-between items-start mb-2">
                            <Badge color="blue">Paper #{i}</Badge>
                            <span className="text-xs text-gray-500">0.8{9-i} Sim</span>
                            </div>
                            <p className="text-xs text-gray-400 line-clamp-2">
                            "Retrieval-augmented generation reduces hallucination by grounding generation..."
                            </p>
                        </div>
                        ))}
                    </GlassCard>
                </div>

                {/* Precision Agent */}
                <div className="flex flex-col gap-4 opacity-75 hover:opacity-100 transition-opacity">
                    <div className="flex items-center gap-2 mb-2">
                        <Filter className="w-5 h-5 text-emerald-400" />
                        <h3 className="text-white font-semibold">Precision Agent</h3>
                    </div>
                    <GlassCard className="flex-1 p-5 overflow-y-auto space-y-4 no-scrollbar">
                        <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                            <p className="text-xs text-emerald-100 italic mb-2">"Source #1 is highly relevant to 'Self-RAG'."</p>
                        </div>
                        <div className="p-3 rounded-xl bg-white/5 border border-white/5 opacity-50">
                            <p className="text-xs text-gray-400">Discarded Source #2: Low relevance score.</p>
                        </div>
                    </GlassCard>
                </div>

                {/* Critic Agent */}
                <div className="flex flex-col gap-4 opacity-75 hover:opacity-100 transition-opacity">
                    <div className="flex items-center gap-2 mb-2">
                        <MessageSquareWarning className="w-5 h-5 text-purple-400" />
                        <h3 className="text-white font-semibold">Critic Agent</h3>
                    </div>
                    <GlassCard className="flex-1 p-5 overflow-y-auto space-y-4 no-scrollbar">
                        <div className="flex gap-3">
                        <div className="mt-1 min-w-[20px] h-5 w-5 rounded-full bg-purple-500/20 flex items-center justify-center text-[10px] text-purple-300 font-bold">!</div>
                        <p className="text-xs text-gray-300">Checking for contradictions in retrieved metrics.</p>
                        </div>
                    </GlassCard>
                </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
};

const PipelineSection = () => {
  const steps = [
    { title: "Query Understanding", icon: Search, desc: "Decomposing complex queries into atomic sub-claims." },
    { title: "Parallel Retrieval", icon: Database, desc: "Multiple agents fetch evidence from diverse indices." },
    { title: "Debate & Critique", icon: MessageSquareWarning, desc: "Agents cross-examine evidence for hallucinations." },
    { title: "Grounded Synthesis", icon: FileText, desc: "Final answer generation cited with verified documents." },
  ];

  return (
    <section id="pipeline" className="py-20 px-6 bg-black/20">
       <div className="max-w-7xl mx-auto">
         <SectionHeading title="The Debate Pipeline" subtitle="From raw query to verified truth through adversarial collaboration." />
         
         <div className="grid md:grid-cols-4 gap-8 relative">
             <div className="hidden md:block absolute top-12 left-0 w-full h-0.5 bg-gradient-to-r from-indigo-500/0 via-indigo-500/50 to-indigo-500/0 z-0" />
             {steps.map((step, idx) => (
               <div key={idx} className="relative z-10 flex flex-col items-center text-center group">
                 <div className="w-24 h-24 rounded-2xl bg-[#0B0B15] border border-white/10 flex items-center justify-center mb-6 group-hover:border-indigo-500/50 transition-colors shadow-xl">
                   <step.icon className="w-8 h-8 text-indigo-400" />
                 </div>
                 <h3 className="text-lg font-bold text-white mb-2">{step.title}</h3>
                 <p className="text-sm text-gray-400">{step.desc}</p>
               </div>
             ))}
         </div>
       </div>
    </section>
  );
};

const ArchitectureSection = () => {
  return (
    <section id="architecture" className="py-24 px-6 relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-500/5 rounded-full blur-3xl -z-10" />
      
      <div className="max-w-5xl mx-auto">
        <SectionHeading 
          title="System Architecture" 
          subtitle="A cyclic, self-correcting reasoning loop designed to minimize hallucinations."
        />
        <div className="relative">
          <div className="absolute left-1/2 -translate-x-1/2 top-0 bottom-0 w-1 bg-gradient-to-b from-indigo-500/0 via-indigo-500/30 to-indigo-500/0 hidden md:block" />
          <div className="flex flex-col items-center gap-12 relative z-10">
            <GlassCard className="p-4 px-8 border-indigo-500/30 shadow-[0_0_30px_rgba(99,102,241,0.15)] flex items-center gap-3">
               <span className="text-gray-400 text-sm font-mono">Input</span>
               <div className="h-6 w-[1px] bg-white/20"></div>
               <span className="text-white font-medium">Complex User Query</span>
            </GlassCard>
            <ArrowDown className="text-gray-600 w-6 h-6 animate-pulse" />
            <div className="relative group">
              <GlassCard className="w-64 p-5 flex flex-col items-center text-center border-purple-500/30 hover:border-purple-400 transition-colors">
                <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center mb-3 text-purple-300">
                  <Bot className="w-6 h-6" />
                </div>
                <h3 className="text-white font-bold mb-1">Planner Agent</h3>
                <p className="text-xs text-gray-400">Decomposes query into atomic sub-questions.</p>
              </GlassCard>
            </div>
            <ArrowDown className="text-gray-600 w-6 h-6 animate-pulse" />
            <div className="relative w-full max-w-4xl p-8 md:p-12 rounded-[3rem] border border-dashed border-white/10 bg-white/[0.02]">
              <div className="absolute top-4 left-6 text-xs font-mono text-indigo-400/60 uppercase tracking-widest">
                Reasoning & Retrieval Loop
              </div>
              <div className="grid md:grid-cols-3 gap-8 items-center">
                <div className="order-3 md:order-1 flex justify-center">
                  <GlassCard className="w-56 p-4 flex flex-col items-center text-center hover:bg-white/10 transition-colors">
                    <div className="p-2 rounded-lg bg-red-500/20 text-red-300 mb-2">
                      <ShieldCheck className="w-5 h-5" />
                    </div>
                    <h4 className="text-white font-bold text-sm">QA Agent</h4>
                    <p className="text-[10px] text-gray-400 mt-1">Validates answers against retrieved evidence.</p>
                  </GlassCard>
                </div>
                <div className="order-1 md:order-2 flex flex-col items-center">
                  <div className="relative z-20">
                      <GlassCard className="w-60 p-6 flex flex-col items-center text-center border-indigo-500 shadow-[0_0_40px_rgba(79,70,229,0.2)] bg-indigo-900/20">
                         <div className="w-14 h-14 rounded-full bg-indigo-500 flex items-center justify-center mb-3 shadow-lg shadow-indigo-500/50 text-white">
                           <BrainCircuit className="w-7 h-7" />
                         </div>
                         <h3 className="text-white font-bold text-lg">Step Definer</h3>
                         <p className="text-xs text-indigo-200 mt-1">Evaluates progress & decides next action.</p>
                      </GlassCard>
                  </div>
                  <div className="mt-3 flex items-center gap-2 text-xs text-gray-500">
                    <Activity className="w-3 h-3" />
                    <span>Dynamic Iterations</span>
                  </div>
                </div>
                <div className="order-2 md:order-3 flex flex-col gap-4">
                  <GlassCard className="w-56 p-4 flex flex-col items-center text-center hover:bg-white/10 transition-colors">
                    <div className="p-2 rounded-lg bg-blue-500/20 text-blue-300 mb-2">
                      <Search className="w-5 h-5" />
                    </div>
                    <h4 className="text-white font-bold text-sm">Retrieval Tool</h4>
                    <p className="text-[10px] text-gray-400 mt-1">Fetches docs from vector store.</p>
                  </GlassCard>
                  <div className="h-6 w-full flex justify-center items-center">
                    <ArrowDown className="text-gray-700 w-4 h-4" />
                  </div>
                  <GlassCard className="w-56 p-4 flex flex-col items-center text-center hover:bg-white/10 transition-colors">
                    <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-300 mb-2">
                      <ScanText className="w-5 h-5" />
                    </div>
                    <h4 className="text-white font-bold text-sm">Extractor</h4>
                    <p className="text-[10px] text-gray-400 mt-1">Parses key context from chunks.</p>
                  </GlassCard>
                </div>
              </div>
              <div className="hidden md:block absolute inset-0 pointer-events-none">
                 <svg className="absolute inset-0 w-full h-full stroke-gray-700/50" fill="none">
                    <path d="M 540 160 Q 650 160 650 180" strokeWidth="2" strokeDasharray="6 6" markerEnd="url(#arrowhead)" />
                    <path d="M 600 400 Q 300 450 250 250" strokeWidth="2" strokeDasharray="6 6" />
                    <path d="M 280 200 Q 350 160 390 160" strokeWidth="2" strokeDasharray="6 6" markerEnd="url(#arrowhead)" />
                    <defs>
                      <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="0" refY="3.5" orient="auto">
                        <polygon points="0 0, 10 3.5, 0 7" fill="#4b5563" />
                      </marker>
                    </defs>
                 </svg>
              </div>
            </div>
            <ArrowDown className="text-gray-600 w-6 h-6 animate-pulse" />
            <GlassCard className="p-1 rounded-3xl bg-gradient-to-r from-emerald-400/20 to-blue-400/20 border-emerald-500/30">
               <div className="bg-[#0B0B15] px-10 py-6 rounded-[1.4rem] flex items-center gap-4">
                  <div className="p-3 bg-emerald-500 rounded-full text-white shadow-lg shadow-emerald-500/30">
                    <CheckCircle2 className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="text-white font-bold text-lg">Final Answer</h3>
                    <p className="text-gray-400 text-sm">Synthesized, verified, and cited response.</p>
                  </div>
               </div>
            </GlassCard>
          </div>
        </div>
      </div>
    </section>
  );
};

const Footer = () => (
  <footer className="py-12 px-6 border-t border-white/5 bg-[#05050A]">
    <div className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
      <div className="text-gray-500 text-sm">
        © 2024 DebateRAG Research Group. MIT License.
      </div>
      <div className="flex gap-6">
        <a href="#" className="text-gray-500 hover:text-white text-sm transition-colors">Documentation</a>
        <a href="#" className="text-gray-500 hover:text-white text-sm transition-colors">GitHub</a>
        <a href="#" className="text-gray-500 hover:text-white text-sm transition-colors">Paper</a>
      </div>
    </div>
  </footer>
);

function App() {
  return (
    <div className="min-h-screen bg-[#0B0B15] text-white selection:bg-indigo-500/30 font-sans">
      <Navbar />
      <Hero />
      <PipelineSection />
      <ArchitectureSection />
      <DemoInterface />
      <Footer />
    </div>
  );
}

export default App;