
from fastembed import TextEmbedding

print("Loading FastEmbed model...")

model = TextEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

texts = [
    "VivPay is an AI-powered financial operations platform.",
    "Customers can check their transaction status."
]

embeddings = list(model.embed(texts))

print("SUCCESS: FastEmbed is working!")
print("Number of embeddings:", len(embeddings))
print("Embedding dimensions:", len(embeddings[0]))
