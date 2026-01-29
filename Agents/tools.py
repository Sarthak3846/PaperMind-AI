import json 
from rank_bm25 import BM25Okapi

class ResearchToolbox:
    def __init__(self,json_path="C:\\Users\\sarth\\OneDrive\\Desktop\\debateRAG.ai\\debateRAG.ai\\pipeline\\processed_papers.json"):
        with open(json_path, 'r') as f:
            self.data = json.load(f)
        corpus = [chunk['content'].split(" ") for chunk in self.data]
        self.bm25 = BM25Okapi(corpus) 
    def search_papers(self,query,top_k=5):
        tokenized_query = query.split(" ")
        results = self.bm25.get_top_n(tokenized_query, self.data, n=top_k)
        formatted_results = ""
        for idx, res in enumerate(results):
            formatted_results += f"--- Result {idx+1} (Source: {res['source']}) ---\n"
            formatted_results += f"{res['content']}\n\n"
            
        return formatted_results

# Initialize the tool globally to be used by agents
toolbox = ResearchToolbox()