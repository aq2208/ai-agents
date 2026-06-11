from openai import OpenAI
import numpy as np

client = OpenAI()

# OpenAI batch embedding
texts = ["First document", "Second document", "Third document"]
response = client.embeddings.create(
    model="text-embedding-3-small",
    input=texts  # Pass a list instead of a single string
)
embeddings = [item.embedding for item in response.data]

print(embeddings)