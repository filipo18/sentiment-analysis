"""Weaviate service for vector search and Q&A on comments.

This service is lazy-initialized and reads configuration directly from env
to avoid coupling with app.config. It will not crash app import if Weaviate
is unavailable; methods handle errors gracefully and return safe defaults.
"""
from __future__ import annotations

import os
import logging
from typing import Any, Dict, List, Optional


class _LazyWeaviateClient:
    """Lazily create a Weaviate client only when first used.

    Avoids import-time failures if Weaviate or network is unavailable.
    """

    def __init__(self) -> None:
        self._client = None
        self._logger = logging.getLogger("app.weaviate_client")

    def get(self):
        if self._client is not None:
            return self._client
        try:
            import weaviate

            url = os.getenv("WEAVIATE_URL", "http://localhost:8080")
            api_key = os.getenv("WEAVIATE_API_KEY", "")
            openai_key = os.getenv("OPENAI_API_KEY", "")

            # Debug: print what we're getting
            print(f"[DEBUG] WEAVIATE_URL: {url}")
            print(f"[DEBUG] WEAVIATE_API_KEY: {'***' + api_key[-4:] if api_key else 'EMPTY'}")
            print(f"[DEBUG] OPENAI_API_KEY: {'***' + openai_key[-4:] if openai_key else 'EMPTY'}")

            auth = weaviate.AuthApiKey(api_key=api_key) if api_key else None
            headers = {"X-OpenAI-Api-Key": openai_key} if openai_key else {}

            self._client = weaviate.Client(
                url=url,
                auth_client_secret=auth,
                additional_headers=headers or None,
            )
            return self._client
        except Exception as e:  # pragma: no cover - defensive
            self._logger.warning(f"Weaviate client init failed: {e}")
            return None


class WeaviateService:
    """Service for Weaviate vector operations (robust, non-failing API)."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("app.weaviate_service")
        self._client_holder = _LazyWeaviateClient()

    # ---------- Schema ----------
    def _ensure_schema(self) -> bool:
        client = self._client_holder.get()
        if client is None:
            return False
        try:
            if client.schema.exists("Comment"):
                return True

            schema = {
                "class": "Comment",
                "description": "Reddit comments with metadata",
                "vectorizer": "text2vec-openai",
                "moduleConfig": {
                    "text2vec-openai": {
                        "model": "text-embedding-3-small",
                        "type": "text",
                    }
                },
                "properties": [
                    {"name": "comment_id", "dataType": ["int"], "description": "Supabase id"},
                    {"name": "brand_name", "dataType": ["string"]},
                    {"name": "product_name", "dataType": ["string"]},
                    {"name": "comment_text", "dataType": ["text"]},
                    {"name": "comment_sentiment", "dataType": ["string"]},
                    {"name": "comment_timestamp", "dataType": ["string"]},
                    {"name": "thread_name", "dataType": ["string"]},
                    {"name": "upvotes", "dataType": ["int"]},
                    {"name": "attribute_discussed", "dataType": ["string"]},
                    {"name": "attribute_sentiment", "dataType": ["string"]},
                ],
            }
            client.schema.create_class(schema)
            return True
        except Exception as e:
            self.logger.warning(f"_ensure_schema failed: {e}")
            return False

    # ---------- Ingest ----------
    def add_comment(self, comment_data: Dict[str, Any]) -> bool:
        client = self._client_holder.get()
        if client is None:
            return False
        if not self._ensure_schema():
            return False
        try:
            data_object = {
                "comment_id": comment_data.get("id"),
                "brand_name": comment_data.get("brand_name") or "",
                "product_name": comment_data.get("product_name") or "",
                "comment_text": comment_data.get("comment") or "",
                "comment_sentiment": comment_data.get("comment_sentiment") or "",
                "comment_timestamp": comment_data.get("comment_timestamp") or "",
                "thread_name": comment_data.get("thread_name") or "",
                "upvotes": comment_data.get("upvotes") or 0,
                "attribute_discussed": comment_data.get("attribute_discussed") or "",
                "attribute_sentiment": comment_data.get("attribute_sentiment") or "",
            }
            client.data_object.create(data_object=data_object, class_name="Comment")
            return True
        except Exception as e:
            self.logger.warning(f"add_comment failed: {e}")
            return False

    def add_comments_batch(self, comments: List[Dict[str, Any]]) -> int:
        success = 0
        for c in comments:
            if self.add_comment(c):
                success += 1
        return success

    # ---------- Query ----------
    def search_comments(
        self, query: str, limit: int = 10, where_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        client = self._client_holder.get()
        if client is None:
            return []
        if not self._ensure_schema():
            return []
        try:
            qb = (
                client.query.get(
                    "Comment",
                    [
                        "comment_id",
                        "brand_name",
                        "product_name",
                        "comment_text",
                        "comment_sentiment",
                        "comment_timestamp",
                        "thread_name",
                        "upvotes",
                        "attribute_discussed",
                        "attribute_sentiment",
                    ],
                )
                .with_near_text({"concepts": [query]})
                .with_limit(max(1, int(limit)))
                .with_additional(["certainty", "distance"])
            )
            if where_filter:
                qb = qb.with_where(where_filter)
            res = qb.do() or {}
            items = (((res.get("data") or {}).get("Get") or {}).get("Comment") or [])
            out: List[Dict[str, Any]] = []
            for it in items:
                add = it.get("_additional") or {}
                out.append(
                    {
                        "comment_id": it.get("comment_id"),
                        "brand_name": it.get("brand_name"),
                        "product_name": it.get("product_name"),
                        "comment_text": it.get("comment_text"),
                        "comment_sentiment": it.get("comment_sentiment"),
                        "comment_timestamp": it.get("comment_timestamp"),
                        "thread_name": it.get("thread_name"),
                        "upvotes": it.get("upvotes"),
                        "attribute_discussed": it.get("attribute_discussed"),
                        "attribute_sentiment": it.get("attribute_sentiment"),
                        "similarity_score": add.get("certainty", 0),
                    }
                )
            return out
        except Exception as e:
            self.logger.warning(f"search_comments failed: {e}")
            return []

    def answer_question(self, question: str, limit: int = 5) -> Dict[str, Any]:
        """Simple Q&A: return top results and a summarized answer via OpenAI if available."""
        results = self.search_comments(question, limit=limit)
        if not results:
            return {
                "answer": "No relevant comments found or vector store unavailable.",
                "relevant_comments": [],
                "sources": 0,
            }

        # Build a compact context
        context_lines = []
        for r in results:
            text = (r.get("comment_text") or "").strip()
            brand = r.get("brand_name") or ""
            product = r.get("product_name") or ""
            context_lines.append(f"[{brand} {product}] {text}")
        context = "\n".join(context_lines[:10])

        openai_key = os.getenv("OPENAI_API_KEY", "")
        if not openai_key:
            # Fallback: return concatenated summary without calling LLM
            snippet = " \n".join(context_lines[:3])
            return {
                "answer": f"Top findings based on similar comments:\n{snippet}",
                "relevant_comments": results,
                "sources": len(results),
            }

        try:
            from openai import OpenAI

            client = OpenAI(api_key=openai_key)
            prompt = (
                "Summarize the following Reddit comments to answer the user question."
                " Be concise and factual.\n\n"
                f"Comments:\n{context}\n\nQuestion: {question}"
            )
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300,
            )
            answer = resp.choices[0].message.content
        except Exception as e:
            self.logger.warning(f"LLM fallback due to error: {e}")
            answer = "\n- " + "\n- ".join(context_lines[:3])

        return {"answer": answer, "relevant_comments": results, "sources": len(results)}

    def get_stats(self) -> Dict[str, Any]:
        client = self._client_holder.get()
        if client is None:
            return {"total_comments": 0, "status": "unavailable"}
        try:
            res = client.query.aggregate("Comment").with_meta_count().do() or {}
            count = 0
            if res.get("data") and res["data"].get("Aggregate") and res["data"]["Aggregate"].get("Comment"):
                count = res["data"]["Aggregate"]["Comment"][0]["meta"]["count"]
            return {"total_comments": count, "status": "connected"}
        except Exception as e:
            self.logger.warning(f"get_stats failed: {e}")
            return {"total_comments": 0, "status": "error", "error": str(e)}


# Global instance
weaviate_service = WeaviateService()


