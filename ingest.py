from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
import chromadb
import os, glob
from dotenv import load_dotenv

load_dotenv()

def get_embeddings():
    # Import here so it loads only when needed, not at startup
    from langchain_community.embeddings import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

def ingest_docs(docs_folder="./docs"):
    documents = []

    for pdf_path in glob.glob(f"{docs_folder}/*.pdf"):
        try:
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            total = " ".join(d.page_content for d in docs).strip()
            if len(total.replace(" ", "").replace("\n", "")) > 50:
                documents.extend(docs)
                print(f"Loaded {pdf_path}: {len(total)} chars")
            else:
                print(f"PDF has no readable text: {pdf_path}")
        except Exception as e:
            print(f"Failed to load {pdf_path}: {e}")

    for txt_path in glob.glob(f"{docs_folder}/*.txt"):
        try:
            loader = TextLoader(txt_path, encoding="utf-8")
            documents.extend(loader.load())
        except Exception as e:
            print(f"Failed to load {txt_path}: {e}")

    if not documents:
        print("No content extracted!")
        return None

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_documents(documents)
    print(f"Created {len(chunks)} chunks")

    embeddings = get_embeddings()
    client = chromadb.EphemeralClient()
    vectorstore = Chroma(
        client=client,
        collection_name="rag_docs",
        embedding_function=embeddings,
    )
    vectorstore.add_documents(chunks)
    print(f"Ingested {len(chunks)} chunks into memory.")
    return vectorstore

if __name__ == "__main__":
    ingest_docs()
