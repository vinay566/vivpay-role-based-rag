
from statement_processor import process_statement

file_path = input("Enter bank statement file path: ").strip()

try:
    with open(file_path, "rb") as file:
        file_bytes = file.read()

    extracted_text = process_statement(
        filename=file_path,
        file_bytes=file_bytes
    )

    print("\n===== BANK STATEMENT EXTRACTION =====")
    print(extracted_text[:3000])

    print("\nStatement extraction successful!")

except Exception as error:
    print("Processing Error:", error)
