"""
CommerceMind VoiceCare AI — Chroma Vector Store Service
Handles policy document embedding and RAG retrieval.
"""

import os
import structlog
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


class ChromaService:
    """Service for policy document storage and retrieval using Chroma."""

    def __init__(self):
        self.persist_dir = settings.chroma_persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Create or get the policy collection
        self.collection = self.client.get_or_create_collection(
            name="policy_documents",
            metadata={"description": "E-commerce company policy documents for RAG"}
        )

    def add_policy(
        self, policy_id: str, title: str, category: str, content: str
    ) -> None:
        """Add or update a policy document in the vector store."""
        self.collection.upsert(
            ids=[policy_id],
            documents=[content],
            metadatas=[{"title": title, "category": category}],
        )
        logger.info("policy_added", policy_id=policy_id, title=title)

    def query_policies(
        self, query: str, n_results: int = 3, category_filter: str = None
    ) -> List[dict]:
        """
        Retrieve the top-N most relevant policy documents for a query.
        This is the RAG retrieval step.
        """
        where_filter = None
        if category_filter:
            where_filter = {"category": category_filter}

        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter,
        )

        policies = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0
                policies.append({
                    "content": doc,
                    "title": metadata.get("title", "Unknown"),
                    "category": metadata.get("category", "General"),
                    "relevance_score": 1 - distance,  # Convert distance to similarity
                })

        logger.info(
            "policy_retrieval",
            query_length=len(query),
            results_count=len(policies),
        )
        return policies

    def get_policy_context(self, query: str, n_results: int = 3) -> str:
        """
        Get formatted policy context string for the resolution LLM call.
        """
        policies = self.query_policies(query, n_results)

        if not policies:
            return "No relevant policy documents found."

        context_parts = []
        for i, policy in enumerate(policies, 1):
            context_parts.append(
                f"--- Policy {i}: {policy['title']} ({policy['category']}) ---\n"
                f"{policy['content']}\n"
                f"(Relevance: {policy['relevance_score']:.2f})"
            )

        return "\n\n".join(context_parts)

    def ingest_policies(self, policies: List[dict]) -> int:
        """Bulk ingest policy documents."""
        count = 0
        for policy in policies:
            self.add_policy(
                policy_id=policy["id"],
                title=policy["title"],
                category=policy["category"],
                content=policy["content"],
            )
            count += 1

        logger.info("policies_ingested", count=count)
        return count

    def get_collection_count(self) -> int:
        """Get the number of documents in the policy collection."""
        return self.collection.count()


# Singleton
_chroma_service: Optional[ChromaService] = None


def get_chroma_service() -> ChromaService:
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaService()
    return _chroma_service
