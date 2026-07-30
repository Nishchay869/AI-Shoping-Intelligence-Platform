"""Runs the same query, over the same embeddings, against ChromaDB, FAISS, and Qdrant side by side.

Pinecone is excluded here since it needs a real account (see pinecone_demo.py). At this corpus size (22
documents) every backend does an *exact* search, so the three should agree almost exactly - which is
itself the point: the vector database you pick changes operational characteristics (hosting model,
persistence, filtering, scaling), not the underlying math. They diverge in practice mainly at large scale,
where most of them switch to an *approximate* nearest-neighbor index (HNSW, IVF, ...) that trades a sliver
of recall for a large speedup.

Run from backend/: python -m vectordb_tutorial.compare
"""
from vectordb_tutorial import chroma_demo, faiss_demo, qdrant_demo
from qdrant_client import QdrantClient

QUERIES = [
    ("how long does the battery last", None),
    ("is it waterproof", "specification"),
    ("comfortable for long wear", "review"),
]


def main() -> None:
    print("Indexing the same 22 documents into ChromaDB, FAISS, and Qdrant...\n")
    chroma_collection = chroma_demo.build_collection()
    faiss_index, faiss_documents = faiss_demo.build_index()
    qdrant_client = QdrantClient(":memory:")
    qdrant_demo.build_collection(qdrant_client)

    for query, doc_type in QUERIES:
        where = {"type": doc_type} if doc_type else None
        print(f"=== Query: '{query}'" + (f" (type={doc_type})" if doc_type else "") + " ===")

        for backend_name, results in [
            ("ChromaDB", chroma_demo.search(chroma_collection, query, top_k=3, where=where)),
            ("FAISS", faiss_demo.search(faiss_index, faiss_documents, query, top_k=3, doc_type=doc_type)),
            ("Qdrant", qdrant_demo.search(qdrant_client, query, top_k=3, doc_type=doc_type)),
        ]:
            top = ", ".join(f"{doc_id} ({similarity:.3f})" for doc_id, _text, similarity, _meta in results)
            print(f"  {backend_name:<10} {top}")
        print()


if __name__ == "__main__":
    main()
