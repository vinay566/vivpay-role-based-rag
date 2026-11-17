
from statement_processor import process_statement
from statement_rag import get_statement_answer


file_path = input("Enter bank statement file path: ").strip()

try:
    with open(file_path, "rb") as file:
        file_bytes = file.read()

    statement_text = process_statement(
        filename=file_path,
        file_bytes=file_bytes
    )

    print("\nStatement processed successfully!")

    question = input(
        "\nAsk a question about your bank statement: "
    ).strip()

    result = get_statement_answer(
        question=question,
        statement_text=statement_text
    )

    print("\n===== VIVPAY STATEMENT RAG ANSWER =====")
    print(result["answer"])

    print("\nSources:")
    for source in result["sources"]:
        print("-", source)

except Exception as error:
    print("\nError:", error)
