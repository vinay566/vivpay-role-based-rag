
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from rag_pipeline import embeddings, llm


# ==========================================
# 1. FORMAT CONVERSATION HISTORY
# ==========================================

def format_history(chat_history):

    conversation = []

    for message in chat_history[-10:]:

        role = message.get("role", "")
        content = message.get("content", "")

        if role in ["user", "assistant"] and content:
            conversation.append(
                f"{role.upper()}: {content}"
            )

    return "\n".join(conversation)


# ==========================================
# 2. GENERATE STATEMENT ANSWER
# ==========================================

def get_statement_answer(
    question,
    statement_text,
    chat_history=None
):

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if not statement_text or not statement_text.strip():
        raise ValueError("No bank statement data provided.")

    chat_history = chat_history or []

    conversation = format_history(chat_history)

    # Split statement into smaller documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120
    )

    documents = splitter.create_documents(
        [statement_text]
    )

    if not documents:
        raise ValueError("Unable to read statement content.")

    # Build temporary vector database
    vectorstore = FAISS.from_documents(
        documents,
        embeddings
    )

    # Retrieve relevant statement information
    retrieval_query = (
        f"{conversation}\nCURRENT QUESTION: {question}"
        if conversation else question
    )

    retriever = vectorstore.as_retriever(
        search_kwargs={"k": 3}
    )

    relevant_documents = retriever.invoke(
        retrieval_query
    )

    context = "\n\n".join(
        document.page_content
        for document in relevant_documents
    )

    prompt = f"""
You are VivPay's Bank Statement AI Assistant.

Your job is to answer questions using the uploaded bank
statement and the previous conversation.

PREVIOUS CONVERSATION:
{conversation if conversation else "No previous conversation."}

CURRENT QUESTION:
{question}

UPLOADED BANK STATEMENT CONTEXT:
{context}

IMPORTANT RULES:

1. Use the uploaded statement as the source of transaction facts.
2. Never invent transactions, dates, amounts or merchant names.
3. If asked "What was my last question?", repeat the latest
   USER question from the previous conversation.
4. If asked "What was my last transaction?", identify the
   most recent transaction in the uploaded statement using
   its transaction date, not the order of retrieved text chunks.
5. If asked a follow-up such as "Tell me more about it",
   use the previous conversation to understand the reference.
6. If the required transaction is not present in the context,
   say that you cannot identify it from the available statement data.
7. Distinguish between transaction date and statement date.
8. Do not expose information from another conversation or statement.
9. Give clear and simple answers.

ANSWER:
"""

    response = llm.invoke(prompt)

    return {
        "answer": response.content,
        "sources": ["Uploaded Bank Statement"]
    }
