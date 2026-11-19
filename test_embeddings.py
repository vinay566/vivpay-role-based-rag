
import os
import numpy as np
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Load environment variables
load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise ValueError("HF_TOKEN not found in .env file")

# Connect to Hugging Face
client = InferenceClient(token=HF_TOKEN)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

try:
    print("Testing Hugging Face embeddings...")

    result = client.feature_extraction(
        "VivPay is an AI-powered financial operations platform.",
        model=MODEL_NAME
    )

    embedding = np.asarray(result)

    print("SUCCESS: Embeddings generated!")
    print("Embedding shape:", embedding.shape)
    print("Embedding dimensions:", embedding.size)

except Exception as e:
    print("Embedding test failed.")
    print("Error:", str(e))

