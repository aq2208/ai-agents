import tiktoken

# Get the tokenizer for GPT-4o.
# At the time of writing, this maps to the o200k_base tokenizer.
encoder = tiktoken.get_encoding("o200k_base")

text = "Tokenization affects cost and latency."

# Encode text to token IDs
token_ids = encoder.encode(text)
print(f"Token IDs: {token_ids}")
print(f"Number of tokens: {len(token_ids)}")

# Decode back to text
decoded = encoder.decode(token_ids)
print(f"Decoded: {decoded}")

# See individual tokens as strings
tokens = [encoder.decode([tid]) for tid in token_ids]
print(f"Tokens: {tokens}")