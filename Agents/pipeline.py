import os
from agents import Agent
from tools import toolbox

# =============================================================================
# 1. DEFINE THE DEBATE TEAM (AGENTS)
# =============================================================================

# --- AGENT 1: RECALL SPECIALIST (Search) ---
search_agent = Agent(
    name="SearchAgent",
    instruction="""You are a Keyword Extraction Engine.
    GOAL: Convert user questions into optimal BM25 search queries.
    RULES: Output ONLY the search query. No intro. Remove stop words.
    Example Input: "How can we improve a simple rag pipeline?"
    Example Output: improve RAG pipeline optimization strategies pre-retrieval re-ranking
    """
)

# --- AGENT 2: PRECISION ANALYST (The Proponent) ---
reader_agent = Agent(
    name="PrecisionAgent",
    instruction="""You are a Data Extraction Subsystem.
    GOAL: Extract hard facts, metrics, and citations from raw text.
    
    RULES:
    1. List facts only. No fluff.
    2. Format: "- [Fact] (Source: [ID])"
    3. If multiple papers discuss the same topic, list both perspectives.
    """
)

# --- AGENT 3: THE CRITIC (The Opponent) ---
critic_agent = Agent(
    name="CriticAgent",
    instruction="""You are an Adversarial Reviewer.
    
    GOAL: Critique the "Extracted Facts" provided by the Precision Agent relative to the User's Query.
    
    TASKS:
    1. Check for Contradictions: Do two sources say different things?
    2. Check for Relevance: Did the Analyst extract info that doesn't answer the prompt?
    3. Check for Gaps: What is missing?
    
    OUTPUT FORMAT:
    - VALIDATED: [List facts that are strong and relevant]
    - FLAGGED: [List facts that are weak, contradictory, or irrelevant]
    - NOTE: [Any warning about missing context]
    """
)

# --- AGENT 4: THE JUDGE (The Teacher) ---
teacher_agent = Agent(
    name="TeacherAgent",
    instruction="""You are an Executive Research Director.
    
    GOAL: Synthesize a Final Answer based on the "Debate" between the Analyst and the Critic.
    
    RULES:
    1. Trust the 'VALIDATED' facts from the Critic.
    2. Treat 'FLAGGED' facts with caution.
    3. STRUCTURE:
       ## Executive Summary
       (Direct answer, <50 words)
       
       ## Critical Analysis
       (Synthesize the debate. Mention specific metrics and paper names.)
       
       ## Verdict
       (Final conclusion based on strongest evidence.)
    
    4. TONE: Professional, dense, executive. No "Hello" or meta-talk.
    """
)

# --- MANAGER (FIXED: Added Instruction) ---
root_agent = Agent(
    name="Manager",
    instruction="""You are the System Orchestrator. 
    Your goal is to manage the flow of information between the Search, Precision, Critic, and Teacher agents.
    """
)

# =============================================================================
# 2. THE DEBATE PIPELINE
# =============================================================================

def run_research_pipeline(user_query):
    print(f"\n[{root_agent.name}] Received Query: '{user_query}'")
    
    # --- STEP 1: RECALL (Search) ---
    print(f"[{root_agent.name}] 1. Initiating Recall Phase...")
    search_query = search_agent.send_message(f"Query: {user_query}")
    print(f"   -> Keywords: '{search_query.strip()}'")
    
    raw_context = toolbox.search_papers(search_query.strip(), top_k=5)
    if not raw_context:
        return "## Execution Halted\nNo relevant documents found in the knowledge base."

    # --- STEP 2: PRECISION (Extraction) ---
    print(f"[{root_agent.name}] 2. Initiating Precision Phase...")
    candidate_facts = reader_agent.send_message(
        f"Query: {user_query}\n\nRaw Text:\n{raw_context}"
    )
    
    # --- STEP 3: DEBATE (Critique) ---
    print(f"[{root_agent.name}] 3. Initiating Adversarial Critique...")
    critique_report = critic_agent.send_message(
        f"""
        USER QUERY: {user_query}
        
        CANDIDATE FACTS (from Analyst):
        {candidate_facts}
        
        TASK: Critique these facts. Are they relevant? Do they contradict? 
        Separate them into VALIDATED and FLAGGED buckets.
        """
    )
    print(f"   -> Critic Report Generated ({len(critique_report)} chars)")

    # --- STEP 4: SYNTHESIS (Verdict) ---
    print(f"[{root_agent.name}] 4. Finalizing Verdict...")
    final_response = teacher_agent.send_message(
        f"""
        User Query: {user_query}
        
        Phase 1 (Facts):
        {candidate_facts}
        
        Phase 2 (Critique):
        {critique_report}
        
        TASK: Write the final executive response. Resolve any conflicts identified by the Critic.
        """
    )
    
    return final_response