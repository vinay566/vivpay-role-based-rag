
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS


# ==========================================
# 1. LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Read Streamlit Cloud secrets if environment variable is unavailable
if not GROQ_API_KEY:
    try:
        import streamlit as st
        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not configured")


# ==========================================
# 2. PROJECT CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

VECTOR_FOLDER = BASE_DIR / "vectorstore"

ALLOWED_ROLES = ["admin", "customer"]


# ==========================================
# 3. INITIALIZE EMBEDDINGS
# ==========================================

embeddings = FastEmbedEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# ==========================================
# 4. INITIALIZE GROQ LLM
# ==========================================

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    api_key=GROQ_API_KEY
)


# ==========================================
# 5. LOAD ROLE-BASED VECTOR DATABASE
# ==========================================

def load_vectorstore(role):

    if role not in ALLOWED_ROLES:
        raise ValueError("Invalid user role")

    db_path = VECTOR_FOLDER / role

    if not db_path.exists():
        raise FileNotFoundError(
            f"Vector database not found: {db_path}"
        )

    vectorstore = FAISS.load_local(
        str(db_path),
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vectorstore


# ==========================================
# 6. RETRIEVE RELEVANT DOCUMENTS
# ==========================================

def retrieve_documents(role, question):

    vectorstore = load_vectorstore(role)

    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 2}
    )

    documents = retriever.invoke(question)

    return documents


# ==========================================
# 7. GENERATE ANSWER USING GROQ
# ==========================================

def get_answer(role, question):

    if role not in ALLOWED_ROLES:
        raise ValueError("Invalid user role")

    if not question.strip():
        raise ValueError("Question cannot be empty")

    documents = retrieve_documents(role, question)

    if not documents:
        return {
            "answer": "I could not find relevant information in the knowledge base.",
            "sources": []
        }

    context = "\n\n".join(
        doc.page_content for doc in documents
    )

    prompt = f"""
You are VivPay's AI financial assistance assistant.

User role: {role}

Answer the question using ONLY the provided context.

Rules:
1. Do not invent financial policies or information.
2. If the answer is not in the context, clearly say
   that the available knowledge base does not contain
   enough information.
3. Give clear and simple answers.
4. Do not reveal information from another role's
   knowledge base.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

    response = llm.invoke(prompt)

    sources = list(set(
        doc.metadata.get("source", "Unknown")
        for doc in documents
    ))

    return {
        "answer": response.content,
        "sources": sources
    }


# ==========================================
# 8. TEST THE RAG PIPELINE
# ==========================================

if __name__ == "__main__":

    print("\n===== VIVPAY ROLE-BASED RAG =====")

    role = input(
        "Enter role (admin/customer): "
    ).strip().lower()

    question = input(
        "Enter your question: "
    ).strip()

    try:

        result = get_answer(role, question)

        print("\n===== GENERATED ANSWER =====")
        print(result["answer"])

        print("\n===== SOURCE DOCUMENTS =====")

        for source in result["sources"]:
            print("-", source)

    except Exception as error:

        print("\nError:", error)
