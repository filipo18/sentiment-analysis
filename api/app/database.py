"""Database operations using Supabase."""
from typing import Any, Dict, List, Optional
from supabase import Client, create_client
from app.config import get_settings
import logging

settings = get_settings()

class DatabaseService:
    """Service for database operations."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        self.logger = logging.getLogger("app.db_service")
    
    def insert_comment(self, comment_data: Dict[str, Any]) -> bool:
        """Insert a comment into the main_reddit table."""
        try:
            # Ensure required fields are present
            data = dict(comment_data)
            if not data.get("brand_name"):
                data["brand_name"] = "unknown"
            # Some schemas require non-null comment_sentiment; default to empty string
            if "comment_sentiment" not in data:
                data["comment_sentiment"] = ""
            result = self.client.table("main_reddit").insert(data).execute()
            # Log Supabase response for troubleshooting
            self.logger.info(f"Supabase insert status={getattr(result, 'status_code', None)}")
            print(f"[DB] Inserted row status={getattr(result, 'status_code', None)}")
            return True
        except Exception as e:
            print(f"[DB] Failed to insert comment: {e}")
            self.logger.exception(f"Failed to insert comment: {e}")
            return False
    
    def get_comments(
        self, 
        product_name: Optional[str] = None, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get comments from the database."""
        query = self.client.table("main_reddit").select("*")
        
        if product_name:
            query = query.eq("product_name", product_name)
        
        query = query.limit(limit).order("comment_timestamp", desc=True)
        
        result = query.execute()
        
        return {
            "comments": result.data,
            "count": len(result.data)
        }
    
    def get_comments_by_brand(self, brand_name: str, limit: int = 100) -> Dict[str, Any]:
        """Get comments filtered by brand name."""
        query = self.client.table("main_reddit").select("*").eq("brand_name", brand_name)
        query = query.limit(limit).order("comment_timestamp", desc=True)
        
        result = query.execute()
        
        return {
            "comments": result.data,
            "count": len(result.data)
        }
    
    def get_recent_comments(self, limit: int = 100) -> Dict[str, Any]:
        """Get the most recent comments."""
        query = self.client.table("main_reddit").select("*")
        query = query.limit(limit).order("comment_timestamp", desc=True)
        
        result = query.execute()
        
        return {
            "comments": result.data,
            "count": len(result.data)
        }

    def delete_comments_for_product(self, product_name: str) -> int:
        """Delete all comments for a given product_name."""
        try:
            res = self.client.table("main_reddit").delete().eq("product_name", product_name).execute()
            # Not all clients return affected row count; best-effort
            try:
                return getattr(res, "count", 0) or 0
            except Exception:
                return 0
        except Exception as e:
            self.logger.exception(f"Failed to delete comments for product '{product_name}': {e}")
            return 0

    def delete_all_comments(self) -> int:
        """Delete all rows from main_reddit."""
        try:
            res = self.client.table("main_reddit").delete().neq("id", -1).execute()
            try:
                return getattr(res, "count", 0) or 0
            except Exception:
                return 0
        except Exception as e:
            self.logger.exception(f"Failed to delete all comments: {e}")
            return 0

    def update_comment_fields(self, comment_id: int, fields: Dict[str, Any]) -> bool:
        """Update specific fields of a comment row by id."""
        try:
            result = (
                self.client
                .table("main_reddit")
                .update(fields)
                .eq("id", comment_id)
                .execute()
            )
            self.logger.info(f"Supabase update id={comment_id} status={getattr(result, 'status_code', None)}")
            return True
        except Exception as e:
            self.logger.exception(f"Failed to update comment id={comment_id}: {e}")
            return False

    def get_top_reddit_channel(self) -> Optional[str]:
        """Return the channel_id of the highest-ranked Reddit source from SourceChannel table.

        Expects a Supabase table named 'source_channel' (or 'source_channels') with fields:
        - platform: 'reddit'
        - channel_id: subreddit name
        - meta_data: JSON containing optional 'score' number
        """
        tables_to_try = ["source_channel", "source_channels"]
        for table in tables_to_try:
            try:
                result = self.client.table(table).select("channel_id, meta_data").eq("platform", "reddit").limit(200).execute()
                rows = result.data or []
                if not rows:
                    continue
                # Compute top by meta_data.score
                def score_of(row: Dict[str, Any]) -> float:
                    meta = row.get("meta_data") or {}
                    try:
                        return float(meta.get("score", 0) or 0)
                    except Exception:
                        return 0.0
                top = max(rows, key=score_of)
                cid = top.get("channel_id")
                if isinstance(cid, str) and cid:
                    return cid
            except Exception:
                # Try next candidate table
                continue
        return None

    def get_top_reddit_channels(self, limit: int = 2) -> List[str]:
        """Return up to 'limit' subreddit names ranked by meta_data.score.

        Falls back to an empty list if no table/rows found.
        """
        try:
            # Accumulate candidates from possible table names
            tables_to_try = ["source_channel", "source_channels"]
            scored_channels: List[tuple[str, float]] = []
            seen: set[str] = set()
            for table in tables_to_try:
                try:
                    result = self.client.table(table).select("channel_id, meta_data").eq("platform", "reddit").limit(200).execute()
                    rows = result.data or []
                    for row in rows:
                        cid = row.get("channel_id")
                        if not isinstance(cid, str) or not cid or cid in seen:
                            continue
                        meta = row.get("meta_data") or {}
                        try:
                            score = float(meta.get("score", 0) or 0)
                        except Exception:
                            score = 0.0
                        scored_channels.append((cid, score))
                        seen.add(cid)
                except Exception:
                    # Try next table name
                    continue

            if not scored_channels:
                return []

            scored_channels.sort(key=lambda it: it[1], reverse=True)
            return [cid for cid, _ in scored_channels[: max(0, int(limit))]]
        except Exception:
            return []

    def replace_source_channels(self, platform: str, channels: List[Dict[str, Any]]) -> Dict[str, int]:
        """Replace existing source_channel rows for a platform with provided channels.

        Each channel dict should include: channel_id, name, metrics, score.
        """
        tables_to_try = ["source_channel", "source_channels"]
        deleted = 0
        inserted = 0
        errors = 0
        for table in tables_to_try:
            try:
                # Delete existing rows for platform
                del_res = self.client.table(table).delete().eq("platform", platform).execute()
                try:
                    deleted = getattr(del_res, "count", 0) or deleted
                except Exception:
                    pass

                # Prepare rows for insert
                rows: List[Dict[str, Any]] = []
                for ch in channels:
                    rows.append(
                        {
                            "platform": platform,
                            "channel_id": ch.get("channel_id"),
                            "name": ch.get("name"),
                            "meta_data": {
                                "score": ch.get("score"),
                                "metrics": ch.get("metrics"),
                            },
                        }
                    )

                if not rows:
                    return {"deleted": deleted, "inserted": 0}

                ins_res = self.client.table(table).insert(rows).execute()
                try:
                    inserted = len(getattr(ins_res, "data", []) or [])
                except Exception:
                    # Some clients don't return inserted rows by default; best-effort
                    inserted = len(rows)
                return {"deleted": deleted, "inserted": inserted}
            except Exception as e:
                self.logger.warning(f"replace_source_channels failed for table '{table}': {e}")
                errors += 1
                continue
        # If both attempts failed
        return {"deleted": deleted, "inserted": inserted, "errors": errors}

# Global database service instance
db_service = DatabaseService()
