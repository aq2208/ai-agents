from openai import OpenAI
import numpy as np

client = OpenAI()  # Uses OPENAI_API_KEY from environment

# Generate an embedding for a single text
response = client.embeddings.create(
    model="text-embedding-3-small",
    input="How do I fix a broken pipe?"
)

# Extract the embedding vector
embedding = response.data[0].embedding
print(f"Dimensions: {len(embedding)}")
print(f"First 10 values: {embedding[:10]}")

# Output
# Dimensions: 1536
# First 10 values: [0.00244903564453125, 0.0189056396484375, 0.0135345458984375, 0.0135345458984375, -0.05059814453125, -0.00229644775390625, -0.029998779296875, -0.0138702392578125, -0.0310821533203125, 0.0271148681640625]
