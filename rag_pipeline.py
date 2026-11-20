
import os
from pathlib import Path

from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_community.vectorstores import FAISS


# ==========================================
# 1. ENVIRONMENT CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing.")


# ==========================================
# 2. FASTEMBED INITIALIZATION
# ==========================================

embeddings = FastEmbedEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)


# ==========================================
# 3. GROQ LLM INITIALIZATION
# ==========================================

llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    groq_api_key=GROQ_API_KEY
)


# ==========================================
# 4. LOAD ROLE-BASED FAISS VECTORSTORES
# ==========================================

VECTORSTORE_DIR = BASE_DIR / "vectorstore"

vectorstores = {}

for role in ["admin", "customer"]:

    store_path = VECTORSTORE_DIR / role

    if not store_path.exists():
        raise FileNotFoundError(
            f"Vectorstore not found for {role}: {store_path}"
        )

    vectorstores[role] = FAISS.load_local(
        str(store_path),
        embeddings,
        allow_dangerous_deserialization=True
    )


# ==========================================
# 5. CONVERSATIONAL RAG FUNCTION
# ==========================================

def get_answer(role, question, chat_history=None):

    if chat_history is None:
        chat_history = []

    if role not in vectorstores:
        raise ValueError(f"Invalid role: {role}")

    # Normalize conversation messages
    normalized_history = []

    for message in chat_history[-10:]:

        speaker = message.get("role") or message.get("message_role")
        content = message.get("content", "")

        if speaker in ["user", "assistant"] and content:
            normalized_history.append({
                "role": speaker,
                "content": content
            })

    # ======================================
    # PREVIOUS QUESTION MEMORY
    # ======================================

    normalized_question = question.strip().lower().rstrip("?.! ")

    if normalized_question in [
        "what is my last question",
        "what was my last question",
        "what is my previous question",
        "what was my previous question"
    ]:

        previous_questions = [
            message["content"]
            for message in normalized_history
            if message["role"] == "user"
        ]

        if previous_questions:
            return (
                f'Your previous question was: '
                f'"{previous_questions[-1]}"'
            )

        return "There is no previous question from you in this conversation."

    # ======================================
    # BUILD CONVERSATION CONTEXT
    # ======================================

    history_text = ""

    for message in normalized_history:

        history_text += (
            f'{message["role"].upper()}: '
            f'{message["content"]}\n'
        )

    # ======================================
    # RETRIEVE RELEVANT DOCUMENTS
    # ======================================

    retrieval_query = (
        history_text
        + "\nCurrent question: "
        + question
    )

    vectorstore = vectorstores[role]

    documents = vectorstore.similarity_search(
        retrieval_query,
        k=2
    )

    context = "\n\n".join(
        document.page_content
        for document in documents
    )

    # ======================================
    # GROQ PROMPT
    # ======================================

    prompt = f"""
You are VivPay's AI financial operations assistant.

Your role is: {role}

Answer using the provided knowledge base.

CONVERSATION RULES:

1. Understand the current question using previous messages.
2. Resolve follow-up questions such as:
   "Tell me more about it."
   "Explain that again."
   "What about the previous one?"
3. Remember previous questions and answers.
4. Never invent information.
5. If the knowledge base does not contain the answer,
   clearly explain that the information is unavailable.
6. Keep answers clear and relevant.

KNOWLEDGE BASE:

{context}

PREVIOUS CONVERSATION:

{history_text}

CURRENT USER QUESTION:

{question}

ANSWER:
"""

    response = llm.invoke(prompt)

    return response.content
