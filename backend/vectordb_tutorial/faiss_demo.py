"""FAISS: a C++/Python LIBRARY for efficient similarity search - not a database. It has no built-in
persistence beyond raw index serialization, no metadata storage, and no filtering: search returns integer
row positions and distances, nothing else. Everything a "real" vector database gives you for free (stable
IDs, metadata, filtering) has to be built around it yourself - that's exactly what this module does with a
small parallel Python list mapping row position -> Document. That extra work is the trade for raw speed and
years of tuning Meta has put into its ANN algorithms.

This demo uses IndexFlatIP - an *exact* (brute-force) index, fine at this scale. At millions of vectors
you'd reach for IndexIVFFlat or IndexHNSWFlat instead, which trade a little recall for much faster search -
the same approximate-nearest-neighbor idea every other vector DB in this tutorial uses internally too.

Run from backend/: python -m vectordb_tutorial.faiss_demo
"""
import faiss
import numpy as np
from vectordb_tutorial.data import EMBEDDING_DIMENSIONS, Document, all_documents, embed


def build_index() -> tuple[faiss.IndexFlatIP, list[Document]]:
    """`documents[i]` is the metadata for the vector FAISS stores at row i - FAISS itself only ever knows row i."""
    documents = all_documents()
    vectors = np.array(embed([doc.text for doc in documents]), dtype="float32")
    index = faiss.IndexFlatIP(EMBEDDING_DIMENSIONS)  # inner product on L2-normalized vectors == cosine similarity
    index.add(vectors)
    return index, documents


def search(index: faiss.IndexFlatIP, documents: list[Document], query: str, top_k: int = 5, doc_type: str | None = None) -> list[tuple[str, str, float, dict]]:
    """FAISS has no native filtering, so over-fetch then filter in Python - fine at this scale. At real scale
    you'd maintain a separate index per type, or use FAISS's IDSelector to pre-restrict the search itself."""
    query_vector = np.array(embed([query]), dtype="float32")
    fetch_k = min(top_k * 5 if doc_type else top_k, index.ntotal)
    similarities, indices = index.search(query_vector, fetch_k)

    results = []
    for similarity, row in zip(similarities[0], indices[0]):
        if row == -1: continue
        document = documents[row]
        if doc_type and document.type != doc_type: continue
        results.append((document.id, document.text, float(similarity), document.metadata))
        if len(results) == top_k: break
    return results


if __name__ == "__main__":
    index, documents = build_index()
    print(f"Indexed {index.ntotal} documents into a FAISS IndexFlatIP\n")

    for label, query, doc_type in [
        ("All types", "how long does the battery last", None),
        ("Reviews only", "how long does the battery last", "review"),
        ("Specifications only", "is it waterproof", "specification"),
    ]:
        print(f"--- {label}: '{query}' ---")
        for doc_id, text, similarity, _metadata in search(index, documents, query, doc_type=doc_type):
            print(f"  [{similarity:.3f}] {doc_id}: {text[:90]}")
        print()
