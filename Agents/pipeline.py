import os 
from agents import Agent
from tools import toolbox

search_agent = Agent(
    name = "Search Agent",
    instruction="""You are an expert Research Librarian specializing in AI/ML papers.
    
    Your Goal: Convert a natural language question into a precise search query for a vector database.
    
    Guidelines:
    1. Identify key entities (e.g., "Self-RAG", "REALM", "InternVL", "GlobalQA").
    2. Identify technical concepts (e.g., "ablation study", "retrieval utility", "ISUSE tokens").
    3. Remove stop words and conversational filler.
    4. OUTPUT ONLY THE SEARCH QUERY STRING. Do not add conversational text.
    
    Example:
    Input: "How does Self-RAG use reflection tokens?"
    Output: Self-RAG reflection tokens critique retrieval generation
    """
)

reader_agent = Agent(
    name="PaperReader",
    instruction="""You are a Senior Technical Analyst.
    
    Your Goal: Analyze raw text segments from research papers and extract hard facts.
    
    Guidelines:
    1. You will receive raw text chunks.
    2. Extract SPECIFIC metrics (e.g., "accuracy improved by 4%", "F1 score of 1.51").
    3. Identify architectural components (e.g., "Critic Model", "Generator", "Retriever").
    4. Quote the paper explicitly where possible.
    5. If the chunks mention specific benchmarks (like "Open-QA" or "GlobalQA"), note them.
    6. IGNORE irrelevant text (like headers, footers, or references).
    
    Output Format: Bullet points of technical findings.
    """
)

teacher_agent = Agent(
    name="TeacherAgent",
    instruction="""You are a University Professor in Computer Science.
    
    Your Goal: Explain complex AI concepts to a student using the facts provided by the Analyst.
    
    Guidelines:
    1. Start with a direct answer to the user's question.
    2. Use the technical facts provided by the PaperReader to support your answer.
    3. Use analogies to explain difficult concepts (e.g., compare "Self-RAG" to a student checking their own work).
    4. Structure your response with clear headings.
    5. Cite the paper names if available (e.g., "According to the InternVL paper...").
    """
)

root_agent = Agent(
    name="Manager",
    instruction="""You are the Research Assistant System Controller.
    
    Your Goal: Manage the conversation flow between the User and the sub-agents.
    
    Workflow:
    1. Receive user query.
    2. Command SearchAgent to generate a query.
    3. Command PaperReader to analyze the retrieved data.
    4. Command TeacherAgent to synthesize the final answer.
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
    final_response = teacher_agent.send_message(
        f"""
        User Question: {user_query}
        
        Technical Facts from Analyst:
        {technical_facts}
        
        Task: Create a comprehensive, student-friendly answer.
        """
    )
    
    return final_response