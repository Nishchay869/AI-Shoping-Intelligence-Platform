"""One-off / periodic job: rebuild the shopping assistant's Chroma index from the current Postgres catalog.

Run from backend/ with the venv active and GEMINI_API_KEY configured:
    python -m scripts.reindex_assistant
"""
from app.db.session import SessionLocal
from app.services.assistant.vector_store import reindex


def main() -> None:
    db = SessionLocal()
    try:
        count = reindex(db)
        print(f"Reindexed {count} documents into the shopping assistant's vector store.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
