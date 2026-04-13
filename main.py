from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from query import get_qa_chain, ask_with_fallback
from ingest import ingest_docs
import shutil, os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global chain — rebuilt fresh on every upload
qa_chain = None

class QuestionRequest(BaseModel):
    question: str

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global qa_chain

    # Clear old docs folder
    os.makedirs("./docs", exist_ok=True)
    for f in os.listdir("./docs"):
        try:
            os.remove(os.path.join("./docs", f))
        except Exception:
            pass

    # Save new file
    file_path = f"./docs/{file.filename}"
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    print(f"Saved: {file_path}")

    # Build fresh in-memory index
    vectorstore = ingest_docs("./docs")
    if vectorstore is None:
        return {"error": "Could not extract text from this file. Make sure the PDF has real selectable text."}

    # Build fresh chain from new vectorstore
    qa_chain = get_qa_chain(vectorstore)
    print(f"Chain ready for: {file.filename}")
    return {"message": f"Uploaded and indexed {file.filename}"}

@app.post("/ask")
def ask_question(req: QuestionRequest):
    if not qa_chain:
        return {"error": "No document uploaded yet. Please upload a file first."}
    try:
        result = ask_with_fallback(qa_chain, req.question)
        sources = list({
            doc.metadata.get("source", "")
            for doc in result["source_documents"]
        })
        return {
            "answer": result["result"],
            "sources": sources
        }
    except Exception as e:
        err = str(e)
        if "429" in err or "rate" in err.lower():
            return {"error": "Rate limited. Please wait a moment and try again."}
        return {"error": f"Something went wrong: {err}"}

@app.get("/health")
def health():
    return {"status": "ok"}
