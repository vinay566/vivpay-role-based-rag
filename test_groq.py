
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

# Load API key
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("Groq API key not found!")

# Initialize supported replacement model
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0,
    api_key=api_key
)

# Test Groq
response = llm.invoke(
    "Explain VivPay in one simple sentence."
)

print("\n========== GROQ TEST ==========")
print(response.content)
print("\nGroq connection successful!")
