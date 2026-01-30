import os 
from agents import Agent
from tools import toolbox

# =============================================================================
# 1. DEFINE THE SPECIALIZED AGENTS (OPTIMIZED FOR PROFESSIONAL BREVITY)
# =============================================================================

# --- AGENT 1: THE SEARCH SPECIALIST ---
# Kept mostly the same, but sharpened to avoid conversational search terms
search_agent = Agent(
    name="SearchAgent",
    instruction="""You are a Keyword Extraction Engine.
    
    GOAL: Convert user questions into optimal BM25 search queries.
    
    RULES:
    1. Output ONLY the search query. No intro, no explanations.
    2. Remove stop words (a, the, is, are).
    3. Focus on unique entities (e.g., "Self-RAG", "InternVL", "F1 Score") and technical terms.
    
    Example Input: "How can we improve a simple rag pipeline?"
    Example Output: improve RAG pipeline optimization strategies pre-retrieval re-ranking
    """
)

# --- AGENT 2: THE ANALYST (PaperReader) ---
# STRICTER: Now forced to extract quotes and citations only, preventing "fluff" accumulation early on.
reader_agent = Agent(
    name="PaperReader",
    instruction="""You are a Data Extraction Subsystem.
    
    GOAL: Extract hard facts, metrics, and definitions from the provided text chunks.
    
    RULES:
    1. Do NOT summarize or explain. List facts only.
    2. Format as a strict bulleted list.
    3. Include the Source ID for every fact.
    4. Look for: Architecture names, specific performance metrics (%), and key methodologies.
    
    Example Output:
    - "Self-RAG uses reflection tokens" (Source: 2310.11511v1)
    - "GlobalQA benchmark F1 score is 1.51" (Source: 2510.26205v2)
    """
)

# --- AGENT 3: THE TEACHER (THE EXECUTIVE SUMMARY) ---
# HEAVILY MODIFIED: Removes "friendly" talk. Enforces structure.
teacher_agent = Agent(
    name="TeacherAgent",
    instruction="""You are an Executive Research Assistant. 
    
    GOAL: Synthesize the provided technical facts into a high-density answer.
    
    STRICT FORMATTING RULES:
    1. NO "Hello", "Sure", "Here is the answer", or "Let's dive in." Start directly with the content.
    2. NO meta-commentary (e.g., "The documents suggest..."). State the facts directly.
    3. Structure the response with these exact headers:
       ## Executive Summary
       (A 2-sentence direct answer)
       
       ## Key Technical Findings
       (Bullet points with citations)
       
       ## Methodology/Architecture
       (If applicable, brief explanation of how it works)
    
    4. CITATIONS: You MUST cite the specific paper name or filename when making claims (e.g., [Self-RAG Paper]).
    5. TONE: Professional, objective, and dense.
    """
)

# --- AGENT 4: THE MANAGER ---
# Minor tweak to ensure it passes raw data cleanly.
root_agent = Agent(
    name="Manager",
    instruction="""You are the System Orchestrator.
    
    PROTOCOL:
    1. Get the search query from SearchAgent.
    2. Run the tool to get raw text.
    3. Pass raw text to PaperReader to get a list of facts.
    4. Pass the LIST OF FACTS to TeacherAgent.
    
    CRITICAL: Do not alter the facts. Pass them exactly as the Analyst provides them.
    """
)

def run_research_pipeline(user_query):
    print(f"\n[{root_agent.name}] Received Query: '{user_query}'")
    print(f"[{root_agent.name}] Delegating to SearchAgent...")
    search_query = search_agent.send_message(
        f"User Query: '{user_query}'. Generate a keyword search query."
    )
    print(f" -> Generated search Terms: '{search_query.strip()}'")
    print(f"[{root_agent.name}] searching database (toolbox.search_papers)...")
    raw_context = toolbox.search_papers(search_query.strip(),top_k=5)

    if not raw_context:
        return "I couldnt find any relevant info"
    
    # --- STEP 3: ANALYZE RETRIEVED TEXT ---
    print(f"[{root_agent.name}] Delegating to PaperReader...")
    technical_facts = reader_agent.send_message(
        f"Analyze these raw text chunks specifically for the query '{user_query}':\n\n{raw_context}"
    )
    # Optional: Print facts to console for debugging
    # print(f"   -> Extracted Facts:\n{technical_facts[:200]}...") 

    # --- STEP 4: SYNTHESIZE FINAL ANSWER ---
    print(f"[{root_agent.name}] Delegating to TeacherAgent...")
    
    # We inject a "System Reminder" directly into the final prompt
    final_prompt = f"""
    QUERY: {user_query}
    
    VERIFIED FACTS (From Analyst):
    {technical_facts}
    
    INSTRUCTION: Synthesize these facts into the Final Answer. 
    REMINDER: No pleasantries. No intro. Use '## Executive Summary' and '## Key Technical Findings'.
    """
    
    final_response = teacher_agent.send_message(final_prompt)
    
    return final_response