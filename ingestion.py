
import os
from pathlib import Path

from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader
)

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.vectorstores import FAISS


# ==========================================
# 1. PROJECT PATHS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

ADMIN_FOLDER = BASE_DIR / "data" / "admin"
CUSTOMER_FOLDER = BASE_DIR / "data" / "customer"

VECTOR_FOLDER = BASE_DIR / "vectorstore"


# ==========================================
# 2. LOAD DOCUMENTS
# ==========================================

def load_documents(folder_path, role):

    documents = []

    if not folder_path.exists():
        raise FileNotFoundError(
            f"Folder not found: {folder_path}"
        )

    for file in folder_path.rglob("*"):

        if not file.is_file():
            continue

        extension = file.suffix.lower()

        try:

            if extension == ".txt":

                loader = TextLoader(
                    str(file),
                    encoding="utf-8"
                )

            elif extension == ".pdf":

                loader = PyPDFLoader(str(file))

            else:
                continue

            loaded_docs = loader.load()

            for doc in loaded_docs:

                doc.metadata["role"] = role
                doc.metadata["source"] = file.name

            documents.extend(loaded_docs)

            print(f"Loaded: {file.name}")

        except Exception as error:

            raise RuntimeError(
                f"Failed to load {file.name}: {error}"
            ) from error

    return documents


# ==========================================
# 3. SPLIT DOCUMENTS INTO CHUNKS
# ==========================================

def split_documents(documents):

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120
    )

    chunks = splitter.split_documents(documents)

    return chunks


# ==========================================
# 4. CREATE EMBEDDINGS
# ==========================================

def create_embeddings():

    print("\nLoading HuggingFace embedding model...")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    return embeddings


# ==========================================
# 5. CREATE FAISS VECTOR DATABASE
# ==========================================

def create_vectorstore(chunks, embeddings, role):

    if not chunks:

        raise ValueError(
            f"No document chunks available for {role}"
        )

    vectorstore = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings
    )

    save_path = VECTOR_FOLDER / role

    save_path.mkdir(
        parents=True,
        exist_ok=True
    )

    vectorstore.save_local(str(save_path))

    print(f"\n{role.upper()} vector database created!")
    print(f"Location: {save_path}")
    print(f"Stored chunks: {len(chunks)}")

    return vectorstore


# ==========================================
# 6. MAIN EXECUTION
# ==========================================

def main():

    print("\n================================")
    print(" VIVPAY ROLE-BASED RAG SYSTEM")
    print(" DOCUMENT INGESTION")
    print("================================\n")

    # Load Admin documents
    print("1. Loading Admin documents...")

    admin_docs = load_documents(
        ADMIN_FOLDER,
        "admin"
    )

    # Load Customer documents
    print("\n2. Loading Customer documents...")

    customer_docs = load_documents(
        CUSTOMER_FOLDER,
        "customer"
    )

    print("\nDocument count:")
    print("Admin:", len(admin_docs))
    print("Customer:", len(customer_docs))

    if not admin_docs or not customer_docs:

        raise ValueError(
            "Both Admin and Customer folders must contain documents."
        )

    # Split documents
    print("\n3. Splitting documents...")

    admin_chunks = split_documents(admin_docs)
    customer_chunks = split_documents(customer_docs)

    print("Admin chunks:", len(admin_chunks))
    print("Customer chunks:", len(customer_chunks))

    # Create embeddings
    print("\n4. Creating embeddings...")

    embeddings = create_embeddings()

    # Create Admin vector store
    print("\n5. Creating Admin vector database...")

    create_vectorstore(
        admin_chunks,
        embeddings,
        "admin"
    )

    # Create Customer vector store
    print("\n6. Creating Customer vector database...")

    create_vectorstore(
        customer_chunks,
        embeddings,
        "customer"
    )

    print("\n================================")
    print(" DAY 1 INGESTION COMPLETED!")
    print("================================")


if __name__ == "__main__":
    main()
