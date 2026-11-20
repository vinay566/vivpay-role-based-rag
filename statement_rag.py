
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

from rag_pipeline import embeddings, llm


def get_statement_answer(
    question,
    statement_text,
    chat_history=None
):
    if chat_history is None:
        chat_history = []

    # Normalize previous conversation messages
    normalized_history = []

    for message in chat_history:
        role = message.get("role") or message.get("message_role")
        content = message.get("content", "")

        if role in ["user", "assistant"] and content:
            normalized_history.append({
                "role": role,
                "content": content
            })

    # Handle "What was my last question?" directly
    if question.strip().lower().rstrip("?.! ") in [
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

    # Build conversation context
    history_text = ""

    for message in normalized_history[-10:]:
        history_text += (
            f'{message["role"].upper()}: '
            f'{message["content"]}\n'
        )

    # Create statement vectorstore
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120
    )

    documents = splitter.create_documents([statement_text])

    vectorstore = FAISS.from_documents(
        documents,
        embeddings
    )

    # Include conversation context in retrieval
    retrieval_query = (
        history_text
        + "\nCurrent question: "
        + question
    )

    relevant_docs = vectorstore.similarity_search(
        retrieval_query,
        k=3
    )

    context = "\n\n".join(
        doc.page_content for doc in relevant_docs
    )

    prompt = f"""
You are VivPay Bank Statement AI.

Answer using the uploaded bank statement and conversation history.

RULES:
1. Understand follow-up questions using previous messages.
2. Resolve words such as "it", "that transaction", and "this".
3. Remember previous answers and questions.
4. Never invent transaction details.
5. If information is unavailable, say so.

PREVIOUS CONVERSATION:
{history_text}

BANK STATEMENT DATA:
{context}

CURRENT QUESTION:
{question}

ANSWER:
"""

    response = llm.invoke(prompt)

    return response.content
