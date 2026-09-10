from sentence_transformers import SentenceTransformer


# Load the embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")


def create_embedding(text: str):
    """
    Convert activity description into a numerical vector.
    """

    if not text:
        return []

    embedding = model.encode(text)

    return embedding.tolist()