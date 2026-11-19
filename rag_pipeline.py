
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS


# ==========================================
# 1. ENVIRONMENT CONFIGURATION
# ==========================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

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
# 3. EMBEDDINGS
# ==========================================

embeddings = FastEmbedEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# ==========================================
# 4. GROQ LLM
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

    return FAISS.load_local(
        str(db_path),
        embeddings,
        allow_dangerous_deserialization=True
    )


# ==========================================
# 6. RETRIEVE DOCUMENTS
# ==========================================

def retrieve_documents(role, question):

    vectorstore = load_vectorstore(role)

    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 3}
    )

    return retriever.invoke(question)


# ==========================================
# 7. FORMAT CHAT HISTORY
# ==========================================

def format_chat_history(chat_history):

    recent_history = chat_history[-10:]

    conversation = []

    for message in recent_history:

        role = message.get("role", "")
        content = message.get("content", "")

        if role in ["user", "assistant"] and content:
            conversation.append(
                f"{role.upper()}: {content}"
            )

    return "\n".join(conversation)


# ==========================================
# 8. GENERATE CONVERSATIONAL ANSWER
# ==========================================

def get_answer(role, question, chat_history=None):

    if role not in ALLOWED_ROLES:
        raise ValueError("Invalid user role")

    if not question or not question.strip():
        raise ValueError("Question cannot be empty")

    chat_history = chat_history or []

    conversation = format_chat_history(chat_history)

    # Include history to improve retrieval for follow-up questions.
    retrieval_query = (
        f"{conversation}\nCURRENT QUESTION: {question}"
        if conversation else question
    )

    documents = retrieve_documents(
        role,
        retrieval_query
    )

    context = "\n\n".join(
        document.page_content
        for document in documents
    )

    if not context:
        context = "No relevant knowledge-base documents found."

    prompt = f"""
You are VivPay's AI financial assistance assistant.

USER ROLE:
{role}

PREVIOUS CONVERSATION:
{conversation if conversation else "No previous conversation."}

CURRENT QUESTION:
{question}

KNOWLEDGE BASE CONTEXT:
{context}

INSTRUCTIONS:

1. Understand the current question using the previous conversation.
2. If asked "What was my last question?", repeat the most recent
   USER question from the previous conversation, not the current one.
3. If asked "What was your previous answer?", summarize the previous
   ASSISTANT response.
4. Understand follow-up questions such as:
   - Tell me more.
   - Explain that.
   - What about it?
   - Give more details.
5. Use the knowledge base for policies, procedures and operational facts.
6. Never invent policies, transaction details or financial information.
7. If the knowledge base does not contain enough information for a
   factual policy question, clearly say so.
8. Do not reveal information from another role's knowledge base.
9. Do not claim to remember messages that are not included above.
10. Answer in clear, simple language.

ANSWER:
"""

    response = llm.invoke(prompt)

    sources = list(set(
        document.metadata.get("source", "Unknown")
        for document in documents
    ))

    return {
        "answer": response.content,
        "sources": sources
    }


# ==========================================
# 9. TEST
# ==========================================

if __name__ == "__main__":

    print("\n===== VIVPAY CONVERSATIONAL RAG =====")

    role = input(
        "Enter role (admin/customer): "
    ).strip().lower()

    history = []

    while True:

        question = input("\nYou: ").strip()

        if question.lower() in ["exit", "quit"]:
            break

        try:

            result = get_answer(
                role=role,
                question=question,
                chat_history=history
            )

            print("\nVivPay AI:", result["answer"])

            history.append({
                "role": "user",
                "content": question
            })

            history.append({
                "role": "assistant",
                "content": result["answer"]
            })

        except Exception as error:
            print("Error:", error)
