"""Retrieval for the chat: FAISS over subject profiles and ads. Owner: Van Thong."""


def retrieve(question: str, k: int = 5) -> list[dict]:
    """Return the k most relevant passages as {text, source, score}."""
    raise NotImplementedError