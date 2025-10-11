"""Helper to get OpenAI-assisted subreddit names and query strings."""
from __future__ import annotations

import json
import os
from typing import List

from openai import OpenAI
import openai


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
        prompt: str = (
            "Given these consumer products, suggest 8-12 specific Reddit subreddit names where people would discuss them. "
            "Include both general topic subreddits and brand-specific ones. "
            "Return only subreddit names (without r/ prefix), comma-separated, no explanations. "
            "Examples: technology, smartphones, android, iphone, samsung, apple, gaming, fitness, beauty, skincare. "
            "Products: " + ", ".join(products)
        )
        resp: openai.types.chat.ChatCompletion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        text: str = resp.choices[0].message.content or ""
        names: List[str] = [s.strip().lstrip("r/") for s in text.split(",") if s.strip()]
        return names[:12]