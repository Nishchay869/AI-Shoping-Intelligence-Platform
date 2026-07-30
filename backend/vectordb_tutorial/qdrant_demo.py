"""Qdrant: an open-source vector database written in Rust. Runs as a local server (or a full cluster) in
production, but also has an embedded local mode - `QdrantClient(":memory:")` or `QdrantClient(path=...)` for
on-disk persistence - with the exact same client API, which is what this demo uses so it needs no server.

Gotcha worth knowing up front: Qdrant point IDs must be an unsigned integer or a valid UUID - unlike Chroma
and FAISS, you cannot use an arbitrary string like "product:sony-wh1000xm5" as the ID directly. The fix is
the standard one: derive a stable UUID from your natural ID (`uuid.uuid5`, deterministic - the same input
always produces the same UUID) and keep the original ID in the payload so you can still recover it.

Run from backend/: python -m vectordb_tutorial.qdrant_demo
"""
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams
from vectordb_tutorial.data import EMBEDDING_DIMENSIONS, all_documents, embed

COLLECTION_NAME = "shopping_catalog"
ID_NAMESPACE = uuid.UUID("12345678-1234-5678-1234-567812345678")  # any fixed UUID works; it just seeds uuid5


def stable_point_id(document_id: str) -> str:
    """Deterministic string-id -> UUID mapping, so re-running this script updates the same points rather than duplicating them."""
    return str(uuid.uuid5(ID_NAMESPACE, document_id))


def build_collection(client: QdrantClient):
    if client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)
    client.create_collection(COLLECTION_NAME, vectors_config=VectorParams(size=EMBEDDING_DIMENSIONS, distance=Distance.COSINE))

    documents = all_documents()
    vectors = embed([doc.text for doc in documents])
    points = [
        PointStruct(id=stable_point_id(doc.id), vector=vector, payload={"original_id": doc.id, "type": doc.type, "text": doc.text, **doc.metadata})
        for doc, vector in zip(documents, vectors)
    ]
    client.upsert(COLLECTION_NAME, points=points)


def search(client: QdrantClient, query: str, top_k: int = 5, doc_type: str | None = None) -> list[tuple[str, str, float, dict]]:
    query_vector = embed([query])[0]
    query_filter = Filter(must=[FieldCondition(key="type", match=MatchValue(value=doc_type))]) if doc_type else None
    response = client.query_points(COLLECTION_NAME, query=query_vector, limit=top_k, query_filter=query_filter, with_payload=True)
    return [(point.payload["original_id"], point.payload["text"], point.score, point.payload) for point in response.points]


if __name__ == "__main__":
    client = QdrantClient(":memory:")  # swap for QdrantClient(path="...") to persist to disk, or QdrantClient(url="http://localhost:6333") for a real server
    build_collection(client)
    print(f"Indexed {client.count(COLLECTION_NAME).count} documents into Qdrant\n")

    for label, query, doc_type in [
        ("All types", "how long does the battery last", None),
        ("Reviews only", "how long does the battery last", "review"),
        ("Specifications only", "is it waterproof", "specification"),
    ]:
        print(f"--- {label}: '{query}' ---")
        for doc_id, text, similarity, _payload in search(client, query, doc_type=doc_type):
            print(f"  [{similarity:.3f}] {doc_id}: {text[:90]}")
        print()
