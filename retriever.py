#retriever.py module 

from embedding_model import create_embeddings
from vector_store import collection


def retrieve_documents(query, top_k):
    """
    Retrieve the most relevant document chunks from ChromaDB.

    Args:
        query: User's question as a string.
        top_k: Number of relevant chunks to retrieve.

    Returns:
        list: A list of retrieved document chunks with metadata.
    """

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    # Generate embedding for the user's query
    query_embedding = create_embeddings([query])[0]

    # Search ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k
    )

    retrieved_documents = []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    ids = results["ids"][0]
    distances = results["distances"][0]

    for document, metadata, chunk_id, distance in zip(
        documents,
        metadatas,
        ids,
        distances
    ):

        retrieved_documents.append({
            "evidence_id": f"E{len(retrieved_documents) + 1:03d}",
            "text": document,
            "metadata": metadata,
            "chunk_id": chunk_id,
            "distance": distance
        })

    return retrieved_documents