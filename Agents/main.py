import sys
from pipeline import run_research_pipeline


def main():
    print(" AI RESEARCH ASSISTANT (RAG PIPELINE)")
    print("   Loaded Knowledge Base: 10 Papers")
    print("   Type 'exit' or 'quit' to stop.")

    while True:
        try:
            # 1. Get User Input
            user_query = input(" Ask a question: ").strip()
            
            if not user_query:
                continue
                
            if user_query.lower() in ['exit', 'quit']:
                print("Goodbye! 👋")
                break

            # 2. Run the Agent Pipeline
            print("\n[System] Waking up agents...") 
            response = run_research_pipeline(user_query)

            # 3. Display Result
            print("🎓 FINAL ANSWER:") 
            print(response)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"❌ Error: {e}") 

if __name__ == "__main__":
    main()

    