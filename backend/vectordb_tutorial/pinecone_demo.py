"""Pinecone: a fully managed cloud vector database. There is no embedded/local mode - every operation here
is a network call to Pinecone's service, which handles sharding, replication, and scaling for you in
exchange for giving up self-hosting and paying for the service. This is the one demo in this tutorial that
genuinely cannot run without a real account: sign up at pinecone.io, create an API key, and set
PINECONE_API_KEY before running it. The code below is verified against the installed `pinecone` SDK
(v9 API surface: Pinecone(), ServerlessSpec, has_index/create_index, Index.upsert/query) but the network
calls themselves have not been executed in this environment.

Run from backend/ (after `export PINECONE_API_KEY=...`): python -m vectordb_tutorial.pinecone_demo
"""
import os
from pinecone import Pinecone, ServerlessSpec
from vectordb_tutorial.data import EMBEDDING_DIMENSIONS, all_documents, embed

INDEX_NAME = "shopping-catalog-demo"


def get_client() -> Pinecone:
    api_key = os.environ.get("PINECONE_API_KEY")
    if not api_key:
        raise RuntimeError("Set PINECONE_API_KEY (from your Pinecone project's API Keys page) before running this demo.")
    return Pinecone(api_key=api_key)


def build_index(client: Pinecone):
    """Serverless indexes are provisioned on demand and billed per-use - no capacity to plan ahead of time."""
    if not client.has_index(INDEX_NAME):
        client.create_index(name=INDEX_NAME, dimension=EMBEDDING_DIMENSIONS, metric="cosine", spec=ServerlessSpec(cloud="aws", region="us-east-1"))
    index = client.Index(INDEX_NAME)

    documents = all_documents()
    vectors = embed([doc.text for doc in documents])
    index.upsert(vectors=[
        {"id": doc.id, "values": vector, "metadata": {"type": doc.type, "text": doc.text, **doc.metadata}}
        for doc, vector in zip(documents, vectors)
    ])
    return index


def search(index, query: str, top_k: int = 5, doc_type: str | None = None) -> list[tuple[str, str, float, dict]]:
    query_vector = embed([query])[0]
    query_filter = {"type": {"$eq": doc_type}} if doc_type else None
    response = index.query(vector=query_vector, top_k=top_k, filter=query_filter, include_metadata=True)
    return [(match.id, match.metadata["text"], match.score, match.metadata) for match in response.matches]


if __name__ == "__main__":
    client = get_client()
    index = build_index(client)
    print(f"Indexed documents into Pinecone index '{INDEX_NAME}'\n")

    for label, query, doc_type in [
        ("All types", "how long does the battery last", None),
        ("Reviews only", "how long does the battery last", "review"),
        ("Specifications only", "is it waterproof", "specification"),
    ]:
        print(f"--- {label}: '{query}' ---")
        for doc_id, text, similarity, _metadata in search(index, query, doc_type=doc_type):
            print(f"  [{similarity:.3f}] {doc_id}: {text[:90]}")
        print()
