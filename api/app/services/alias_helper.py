"""Helper to get OpenAI-assisted subreddit names and query strings."""
from __future__ import annotations

import json
import os
from typing import List

from openai import OpenAI


def _load_openai_key() -> str:
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    for p in ["config.json", os.path.join("api", "config.json")]:
        try:
            with open(p, "r", encoding="utf-8") as fh:
                cfg = json.load(fh)
                if cfg.get("openai_api_key"):
                    return cfg["openai_api_key"]
        except Exception:
            continue
    raise RuntimeError("OPENAI_API_KEY not configured; set env var or add config.json")


class AliasHelper:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=_load_openai_key())

    async def suggest_subreddits(self, products: List[str]) -> List[str]:
        prompt = (
            "Given these product names, list up to 8 relevant subreddit names (without r/ prefix), "
            "comma-separated, no explanations. Products: " + ", ".join(products)
        )
        resp = self.client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        text = resp.choices[0].message.content or ""
        names = [s.strip().lstrip("r/") for s in text.split(",") if s.strip()]
        return names[:8]

    async def suggest_reddit_queries(self, products: List[str]) -> List[str]:
        prompt = (
            "Create up to 5 high-signal Reddit search queries for these products. "
            "Return comma-separated queries only. Products: " + ", ".join(products)
        )
        resp = self.client.chat.completions.create(
            model="gpt-5-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        text = resp.choices[0].message.content or ""
        queries = [s.strip() for s in text.split(",") if s.strip()]
        return queries[:5]


