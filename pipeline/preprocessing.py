import re
import json
from pypdf import PdfReader

def preprocess_research_paper(pdf_path):
    reader = PdfReader(pdf_path)
    extracted_text = []

    def visitor_body(text,cm,tm,font_dict,font_size):
        y_coordinate = tm[5]
        if 50<y_coordinate<720:
            extracted_text.append(text)

    for page in reader.pages: #iterate through every page in the pdf
        page.extract_text(visitor_text=visitor_body) #extract text using spatial feature.

    raw_content = "".join(extracted_text) #join the list into a single string
    cleaned_text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', raw_content)
    # Remove multiple newlines and extra spaces caused by column gaps
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text) 
    
    # Remove common academic noise like [1], [12, 15] or (Guu et al., 2020) 
    # Optional: Keep these if you want the LLM to cite specific sources
    cleaned_text = re.sub(r'\[\d+(?:,\s*\d+)*\]', '', cleaned_text)

    return cleaned_text.strip()


def create_chunks(text,chunk_size = 1000,overlap=100):
    #splitting the text into overlapping chunks 
    chunks = []
    for i in range(0,len(text),chunk_size-overlap):
        chunk = text[i:i+chunk_size] #slice string to get chunk
        chunks.append(chunk) #add chunk to chunks list
    return chunks

file_names = [
    "C:\\Users\\sarth\\OneDrive\\Desktop\\debateRAG.ai\\debateRAG.ai\\DATASET\\2002.08909v1.pdf","C:\\Users\\sarth\\OneDrive\\Desktop\\debateRAG.ai\\debateRAG.ai\\DATASET\\2205.10788v2.pdf","C:\\Users\\sarth\\OneDrive\\Desktop\\debateRAG.ai\\debateRAG.ai\\DATASET\\2305.14762v2.pdf",
    "C:\\Users\\sarth\\OneDrive\\Desktop\\debateRAG.ai\\debateRAG.ai\\DATASET\\2310.11511v1.pdf","C:\\Users\\sarth\\OneDrive\\Desktop\\debateRAG.ai\\debateRAG.ai\\DATASET\\2312.10997v5.pdf","C:\\Users\\sarth\\OneDrive\\Desktop\\debateRAG.ai\\debateRAG.ai\\DATASET\\2404.16821v2.pdf",
    "C:\\Users\\sarth\\OneDrive\\Desktop\\debateRAG.ai\\debateRAG.ai\\DATASET\\2410.12837v1.pdf","C:\\Users\\sarth\\OneDrive\\Desktop\\debateRAG.ai\\debateRAG.ai\\DATASET\\2510.26205v2.pdf","C:\\Users\\sarth\\OneDrive\\Desktop\\debateRAG.ai\\debateRAG.ai\\DATASET\\NeurIPS-2020-retrieval-augmented-generation-for-knowledge-intensive-nlp-tasks-Paper.pdf",
    "C:\\Users\\sarth\\OneDrive\\Desktop\\debateRAG.ai\\debateRAG.ai\\DATASET\\ssrn-5252835.pdf"
]

all_paper_chunks = []
for file in file_names:
    print(f"preprocessing: {file}")
    text = preprocess_research_paper(file)
    chunks = create_chunks(text)
    all_paper_chunks.append(chunks)

def save_chunks_to_json(all_chunks,output_file):
    with open(output_file,'w',encoding='utf-8') as f:
        json.dump(all_chunks,f,indent=4)
    print(f"successfully saved {len(all_chunks)} chunks to {output_file}")

processed_data = []
for file in file_names:
    text = preprocess_research_paper(file)
    chunks = create_chunks(text)
    
    for i, chunk_text in enumerate(chunks):
        # Create a dictionary for each chunk to keep track of its source
        entry = {
            "id": f"{file}_{i}",                      # Unique ID for the database
            "source": file,                           # The paper title
            "content": chunk_text,                    # The actual text for embedding
            "chunk_index": i                          # Position in the original paper
        }
        processed_data.append(entry)

save_chunks_to_json(processed_data, "processed_papers.json")