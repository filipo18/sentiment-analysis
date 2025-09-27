"""Sentiment analysis service using OpenAI for Reddit comments."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

from app.database import db_service


ATTRIBUTE_VOCAB: List[str] = [
    "battery life",
    "price",
    "health features",
    "fitness tracking",
    "design",
    "notifications",
    "sleep tracking",
    "ECG",
    "heart rate accuracy",
    "durability",
    "water resistance",
    "charging speed",
    "Siri",
    "apps ecosystem",
    "integration with iPhone",
    "screen brightness",
    "cellular connectivity",
    "Apple Pay",
    "maps/navigation",
    "bands/straps",
    "general",
]


SCHEMA: Dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "sentiment_positive": {"type": "integer", "minimum": 0, "maximum": 100},
        "sentiment_neutral": {"type": "integer", "minimum": 0, "maximum": 100},
        "sentiment_negative": {"type": "integer", "minimum": 0, "maximum": 100},
        "attribute_discussed": {"type": "string"},
        "attribute_sentiment_positive": {"type": "integer", "minimum": 0, "maximum": 100},
        "attribute_sentiment_neutral": {"type": "integer", "minimum": 0, "maximum": 100},
        "attribute_sentiment_negative": {"type": "integer", "minimum": 0, "maximum": 100},
    },
    "required": [
        "sentiment_positive",
        "sentiment_neutral",
        "sentiment_negative",
        "attribute_discussed",
        "attribute_sentiment_positive",
        "attribute_sentiment_neutral",
        "attribute_sentiment_negative",
    ],
}


def _load_openai_key() -> str:
    env_key = os.getenv("OPENAI_API_KEY")
    if env_key:
        return env_key
    # Fallbacks: look for config.json in repo root or api/ directory
    candidate_paths = [
        os.path.join(os.getcwd(), "config.json"),
        os.path.join(os.getcwd(), "api", "config.json"),
    ]
    for path in candidate_paths:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                cfg = json.load(fh)
                key = cfg.get("openai_api_key")
                if key:
                    return key
        except FileNotFoundError:
            continue
        except json.JSONDecodeError:
            continue
    raise RuntimeError("OPENAI_API_KEY not configured; set env var or add config.json")


def _fix_to_100(a: int, b: int, c: int) -> Tuple[int, int, int]:
    total = a + b + c
    if total == 100:
        return a, b, c
    # Adjust the largest bucket by the delta
    vals = [("a", a), ("b", b), ("c", c)]
    key_max = max(vals, key=lambda x: x[1])[0]
    delta = 100 - total
    if key_max == "a":
        a += delta
    elif key_max == "b":
        b += delta
    else:
        c += delta
    return a, b, c


def _classify_from_net(positive: int, negative: int) -> str:
    """Classify sentiment by net score (positive - negative).

    Assumption: negative if net < 40; neutral if 40 <= net <= 60; positive if net > 60.
    """
    net = int(positive) - int(negative)
    if net < 40:
        return "negative"
    if net <= 60:
        return "neutral"
    return "positive"


class AnalysisService:
    def __init__(self) -> None:
        api_key = _load_openai_key()
        self.client = OpenAI(api_key=api_key)

    def _analyze_comment(self, comment: str) -> Dict[str, Any]:
        system = (
            "You are a strict JSON API. "
            "Return only JSON that matches the provided JSON schema. "
            "Produce whole-number percentages (0–100) and make each triad sum to 100. "
            f"Pick the single most-relevant product attribute from this list; if unclear choose 'general': {', '.join(ATTRIBUTE_VOCAB)}."
        )
        user = f'Comment: """{comment}"""'

        resp = self.client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            response_format={
                "type": "json_schema",
                "json_schema": {"name": "Sentiment", "schema": SCHEMA},
            },
        )

        data = json.loads(resp.choices[0].message.content)

        sp, sn, sneg = _fix_to_100(
            int(data["sentiment_positive"]), int(data["sentiment_neutral"]), int(data["sentiment_negative"])  # type: ignore[index]
        )
        ap, an, aneg = _fix_to_100(
            int(data["attribute_sentiment_positive"]), int(data["attribute_sentiment_neutral"]), int(data["attribute_sentiment_negative"])  # type: ignore[index]
        )

        comment_sentiment = _classify_from_net(sp, sneg)
        attribute_sentiment = _classify_from_net(ap, aneg)

        return {
            "comment_sentiment": comment_sentiment,
            "attribute_discussed": data["attribute_discussed"],  # type: ignore[index]
            "attribute_sentiment": attribute_sentiment,
        }

    def analyze_recent_comments(self, limit: int = 100) -> Dict[str, Any]:
        """Analyze up to 'limit' recent comments and update rows with results.

        Updates fields: comment_sentiment, attribute_discussed, attribute_sentiment.
        """
        result = db_service.get_recent_comments(limit=limit)
        comments = result.get("comments", [])

        updated = 0
        skipped = 0
        for row in comments:
            cid = row.get("id")
            text = (row.get("comment") or "").strip()
            if not cid or not text:
                skipped += 1
                continue
            print(f"Analyzing comment {cid}")
            analysis = self._analyze_comment(text)
            print(f"Analysis: {analysis}")
            db_service.update_comment_fields(int(cid), analysis)
            updated += 1

        return {"updated": updated, "skipped": skipped, "total_scanned": len(comments)}


# Global instance
analysis_service = AnalysisService()


