from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from pipeline import run_research_pipeline  # Importing your existing pipeline

app = FastAPI()

# Allow your React app (usually running on localhost:5173) to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Keep this open for now to prevent Vercel errors
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Define the data format we expect from the frontend
class QueryRequest(BaseModel):
    query: str

@app.post("/api/research")
async def research_endpoint(request: QueryRequest):
    try:
        # Run your actual agent pipeline
        print(f"Received query: {request.query}")
        result = run_research_pipeline(request.query)
        return {"status": "success", "answer": result}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

