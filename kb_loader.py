# index_kb.py

import os
import json
from typing import Any, Dict, List

from chromadb.config import Settings
from langchain_chroma import Chroma

from models import build_embedding_model

CHROMA_DB_DIR = "./chroma_db"
KB_PATH = "knowledge_base.json"


def load_knowledge_base(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_index() -> None:
    """Create / reset the Chroma collection and ingest the KB via HF embeddings."""
    os.makedirs(CHROMA_DB_DIR, exist_ok=True)

    # Disable Chroma telemetry spam
    settings = Settings(anonymized_telemetry=False)

    embedding_model = build_embedding_model()
    kb_docs = load_knowledge_base(KB_PATH)

    # Clear previous collection for repeatability
    tmp_store = Chroma(
        collection_name="demo_kb",
        embedding_function=embedding_model,
        persist_directory=CHROMA_DB_DIR,
        client_settings=settings,
    )
    tmp_store.delete_collection()

    # Fresh collection
    vector_store = Chroma(
        collection_name="demo_kb",
        embedding_function=embedding_model,
        persist_directory=CHROMA_DB_DIR,
        client_settings=settings,
    )

    texts = [doc["text"] for doc in kb_docs]
    metadatas = [
        {
            "id": doc["id"],
            "category": doc["category"],
            "client_type": doc["client_type"],
        }
        for doc in kb_docs
    ]

    vector_store.add_texts(texts=texts, metadatas=metadatas)

    print(f"Indexed {len(texts)} documents into Chroma at {CHROMA_DB_DIR}")


if __name__ == "__main__":
    build_index()
