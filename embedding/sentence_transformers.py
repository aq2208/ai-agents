# OpenSource
from sentence_transformers import SentenceTransformer

# Load a popular open-source embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Generate embeddings for multiple texts at once
sentences = [
    "How do I fix a broken pipe?",
    "Plumbing repair guide",
    "Chocolate cake recipe"
]

embeddings = model.encode(sentences)
print(f"Shape: {embeddings.shape}")
print(f"First embedding (first 10 values): {embeddings[0][:10]}")