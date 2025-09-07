import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import json
import uuid


class MemoryStore:
    def __init__(self, path: str = "./chroma_db"):
        # New-style persistent client; turn off telemetry if you want
        self.client = chromadb.PersistentClient(
            path=path,
            settings=Settings(anonymized_telemetry=False)
        )

        # Create or fetch the collection
        self.collection = self.client.get_or_create_collection(name="user_preferences")

    async def save_preference(self, user_id: str, preference: str, metadata: Optional[Dict] = None) -> str:
        """Save user preference to vector store"""
        meta = metadata or {}
        doc_id = str(uuid.uuid4())

        self.collection.add(
            documents=[preference],
            metadatas=[{
                "user_id": user_id,
                "timestamp": meta.get("timestamp", ""),
                "type": meta.get("type", "preference"),
            }],
            ids=[doc_id],
        )
        return doc_id

    async def get_user_preferences(self, user_id: str, limit: int = 5) -> List[str]:
        """Retrieve user preferences"""
        try:
            res = self.collection.get(
                where={"user_id": user_id},
                limit=limit,
                include=["documents"],
            )
            docs = res.get("documents") or []
            # `documents` is a list of lists (batched); flatten the first batch if present
            return docs[0] if docs and isinstance(docs[0], list) else docs
        except Exception:
            return []

    async def save_optimization_run(self, user_id: str, run_data: Dict) -> str:
        """Save optimization run for learning"""
        doc_id = str(uuid.uuid4())
        summary = f"User {user_id} saved €{run_data.get('savings_eur', 0)} by shifting {run_data.get('kwh_flexible', 0)} kWh"

        self.collection.add(
            documents=[summary],
            metadatas=[{
                "user_id": user_id,
                "type": "optimization_run",
                "data": json.dumps(run_data),
            }],
            ids=[doc_id],
        )
        return doc_id
