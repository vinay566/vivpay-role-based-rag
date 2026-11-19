
from rag_pipeline import retrieve_documents, get_answer

print("===== VIVPAY RAG FUNCTION TEST =====")

role = input(
    "Enter role (admin/customer): "
).strip().lower()

question = input(
    "Enter your question: "
).strip()

try:

    # 1. Test document retrieval
    print("\n1. TESTING DOCUMENT RETRIEVAL")

    documents = retrieve_documents(
        role,
        question
    )

    print("Retrieved documents:", len(documents))

    for i, document in enumerate(documents, start=1):

        print(f"\n--- Retrieved Document {i} ---")
        print("Source:", document.metadata.get("source"))
        print("Content:")
        print(document.page_content[:500])

    # 2. Test Groq answer generation
    print("\n2. TESTING GROQ ANSWER GENERATION")

    result = get_answer(
        role,
        question
    )

    print("\nGenerated Answer:")
    print(result["answer"])

    print("\nSources:")
    for source in result["sources"]:
        print("-", source)

    # 3. Test result
    if documents and result["answer"]:
        print("\nRAG PIPELINE EXECUTION SUCCESSFUL!")
    else:
        print("\nRAG PIPELINE RETURNED NO RESULTS.")

except Exception as error:

    print("\nRAG TEST FAILED:")
    print(error)