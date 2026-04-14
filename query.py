from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os, re

load_dotenv()

PROMPT_TEMPLATE = """
You are a helpful assistant. Use ONLY the context below to answer.
If the answer isn't in the context, say "I don't have that info."
Do NOT think out loud. Do NOT show reasoning. Just answer directly.

Context:
{context}

Question: {question}
Answer:"""

def clean_answer(text: str) -> str:
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = text.strip()
    return text if text else "I don't have that info."

def get_llm():
    model = os.getenv("OPENROUTER_MODEL", "openrouter/auto")
    return ChatOpenAI(
        model=model,
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://rag-chat.onrender.com",
            "X-Title": "RAG Chat App",
        },
        temperature=0
    )

def get_qa_chain(vectorstore):
    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE,
        input_variables=["context", "question"]
    )
    chain = RetrievalQA.from_chain_type(
        llm=get_llm(),
        retriever=vectorstore.as_retriever(search_kwargs={"k": 4}),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )
    return chain

def ask_with_fallback(chain, question):
    try:
        result = chain.invoke({"query": question})
        result["result"] = clean_answer(result["result"])
        return result
    except Exception as e:
        err = str(e)
        if "429" in err or "rate" in err.lower():
            raise Exception("Rate limited. Please wait a moment and try again.")
        raise e
