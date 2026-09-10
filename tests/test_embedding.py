from backend.app.matching.embedding import create_embedding


text = "Foundation excavation completed at Area A"

embedding = create_embedding(text)

print("Text:")
print(text)

print("\nVector length:")
print(len(embedding))

print("\nFirst 10 values:")
print(embedding[:10])