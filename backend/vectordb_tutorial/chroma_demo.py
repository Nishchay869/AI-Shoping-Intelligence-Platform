"""ChromaDB: an open-source, developer-friendly vector database. Runs embedded in-process here (backed by
SQLite + a local index on disk) - no server to stand up, which makes it the easiest of the four to get
started with. The same client API also works against a self-hosted or Chroma Cloud server once you outgrow
a single machine; only the client constructor changes (`chromadb.HttpClient(...)` instead of `PersistentClient`).

Run from backend/: python -m vectordb_tutorial.chroma_demo
"""
from pathlib import Path
import chromadb
from vectordb_tutorial.data import all_documents, embed

PERSIST_DIR = Path(__file__).resolve().parent / "storage" / "chroma"
COLLECTION_NAME = "shopping_catalog"


def build_collection():
    """Create (or reset) a collection and add every product/review/spec as one embedding + metadata payload."""
    client = chromadb.PersistentClient(path=str(PERSIST_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.get_or_create_collection(COLLECTION_NAME, metadata={"hnsw:space": "cosine"})

    documents = all_documents()
    vectors = embed([doc.text for doc in documents])
    collection.add(
        ids=[doc.id for doc in documents],
        embeddings=vectors,
        documents=[doc.text for doc in documents],
        metadatas=[{"type": doc.type, **doc.metadata} for doc in documents],
    )
    return collection


def search(collection, query: str, top_k: int = 5, where: dict | None = None) -> list[tuple[str, str, float, dict]]:
    """Embed the query and run cosine similarity search, optionally pre-filtered by metadata (`where`)."""
    query_vector = embed([query])[0]
    results = collection.query(query_embeddings=[query_vector], n_results=top_k, where=where)
    similarities = [1 - distance for distance in results["distances"][0]]  # Chroma returns cosine *distance*
    return list(zip(results["ids"][0], results["documents"][0], similarities, results["metadatas"][0]))


if __name__ == "__main__":
    collection = build_collection()
    print(f"Indexed {collection.count()} documents into ChromaDB ({PERSIST_DIR})\n")

    for label, query, where in [
        ("All types", "how long does the battery last", None),
        ("Reviews only", "how long does the battery last", {"type": "review"}),
        ("Specifications only", "is it waterproof", {"type": "specification"}),
    ]:
        print(f"--- {label}: '{query}' ---")
        for doc_id, text, similarity, _metadata in search(collection, query, where=where):
            print(f"  [{similarity:.3f}] {doc_id}: {text[:90]}")
        print()
