
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


# Project directory
BASE_DIR = Path(__file__).resolve().parent

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True}
)


# Load role-specific vector database
def load_vectorstore(role):

    db_path = BASE_DIR / "vectorstore" / role

    vectorstore = FAISS.load_local(
        str(db_path),
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vectorstore


# Search documents
def search_documents(role, question):

    vectorstore = load_vectorstore(role)

    results = vectorstore.similarity_search(
        question,
        k=2
    )

    print("\n==============================")
    print("ROLE:", role.upper())
    print("QUESTION:", question)
    print("==============================")

    for i, doc in enumerate(results, start=1):

        print(f"\nResult {i}")
        print("Source:", doc.metadata.get("source"))
        print("Content:")
        print(doc.page_content)


# Test Admin retrieval
search_documents(
    "admin",
    "What happens when a fraud alert is critical?"
)


# Test Customer retrieval
search_documents(
    "customer",
    "What should I do if my payment is pending?"
)
