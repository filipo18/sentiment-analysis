"""Sentiment analysis service using OpenAI for Reddit comments."""
from __future__ import annotations

import json
import os
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel
import logging
import time
from app.config import get_settings

from openai import OpenAI, AsyncOpenAI
from app.database import db_service


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


def _classify_from_percentage(percentage: int) -> str:
    """Classify sentiment from a single percentage value (0-100).
    
    Where 0=very negative, 100=very positive
    """
    if percentage <= 20:
        return "negative"
    elif percentage <= 60:
        return "neutral"
    else:  # 81-100
        return "positive"


class CommentAnalysis(BaseModel):
    comment_id: int
    sentiment: int
    attribute_discussed: str
    attribute_sentiment: int

class BatchSentimentResponse(BaseModel):
    analyses: List[CommentAnalysis]

class AnalysisService:
    def __init__(self) -> None:
        api_key = _load_openai_key()
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
        self._attribute_cache: Dict[str, List[str]] = {}  # Product name -> attributes cache

    def _get_product_attributes(self, product_name: str) -> List[str]:
        """Get the top 30 most common attributes for a product, with caching."""
        if product_name in self._attribute_cache:
            return self._attribute_cache[product_name]

        class AttributesResponse(BaseModel):
            attributes: List[str]
        
        try:
            # Extract attributes using OpenAI
            system_prompt = (
                """
                You are an expert product analyst. Given a product name, return the top 30 most commonly discussed attributes or features that people mention when reviewing or discussing this product. Focus specifically on attributes relevant for sentiment analysis. If there are fewer than 30 relevant attributes, return as many as you can find. List the attributes in order of frequency, from most to least mentioned.
                Begin with a concise checklist (3-7 bullets) outlining your planned steps for identifying relevant attributes. Make sure steps are conceptual and not implementation details.
                ## Output Format
                Return ONLY a JSON array of strings. Do not include any explanations or additional text. For example:
                [
                "battery life",
                "screen quality",
                "build quality"
                // ...
                ]
                """
            )
            
            user_prompt = f"Product: {product_name}\n\nReturn the top 30 most discussed attributes as a JSON array."
            
            response = self.client.responses.parse(
                model="gpt-4.1-nano-2025-04-14",
                instructions=system_prompt,
                input=user_prompt,
                text_format=AttributesResponse,
            )
            
            return response.output_parsed.attributes
        except Exception as e:
            logging.error(f"Failed to retrieve attributes for product '{product_name}': {e}")
            return

    async def _analyze_comment(self, comment: str, product_name: str, attributes: List[str]) -> Dict[str, Any]:
        class SentimentResponse(BaseModel):
            sentiment: int  # Overall sentiment percentage (0-100, where 0=very negative, 100=very positive)
            attribute_discussed: str
            attribute_sentiment: int  # Attribute-specific sentiment percentage (0-100)

        instructions = (
            f"""
            You are a sentiment analysis expert. Analyze the given comment for a {product_name} product.
            
            ## Task
            1. Determine overall comment sentiment as a single percentage (0-100, where 0=very negative, 100=very positive)
            2. Identify the most relevant product attribute being discussed from: {', '.join(attributes)}
            3. Determine sentiment specifically for that attribute as a single percentage (0-100)
            
            ## Rules
            - Sentiment percentages: 0-20=negative, 21-40=somewhat negative, 41-60=neutral, 61-80=somewhat positive, 81-100=positive
            - If no specific attribute is clear, use 'general'
             - When the comment expresses preference for a competitor (e.g., mentions liking a different brand more), reflect this as negative sentiment for the given product.
            - Be precise and objective in your analysis
            """
        )
        
        input_text = f"Comment: {comment}"

        response = await self.async_client.responses.parse(
            model="gpt-5-nano-2025-08-07",
            instructions=instructions,
            input=input_text,
            text_format=SentimentResponse,
        )

        data = response.output_parsed

        # Convert percentages to classifications
        comment_sentiment = _classify_from_percentage(data.sentiment)
        attribute_sentiment = _classify_from_percentage(data.attribute_sentiment)

        return {
            "comment_sentiment": comment_sentiment,
            "attribute_discussed": data.attribute_discussed,
            "attribute_sentiment": attribute_sentiment,
        }

    async def _analyze_comments_batch(
        self, 
        comment_batch: List[Dict[str, Any]], 
        product_name: str, 
        attributes: List[str]
    ) -> List[Dict[str, Any]]:
        """Analyze a batch of comments in a single API call."""
        batch_size = len(comment_batch)
        
        # Build batch prompt with header
        comments_text = "Comments to process:\n" + "\n".join([
            f"[{row['id']}] \"{row['comment']}\""
            for row in comment_batch
        ])
        
        instructions = f"""
        You are analyzing {batch_size} comments for {product_name}.
        
        For each comment, provide:
        1. comment_id: The ID number from the brackets
        2. sentiment: 0-100 percentage (0=very negative, 100=very positive)
        3. attribute_discussed: From this list: {', '.join(attributes)}
        4. attribute_sentiment: 0-100 percentage for that specific attribute
        
        Rules:
        - Sentiment percentages: 0-20=negative, 21-60=neutral, 61-100=positive
        - If no specific attribute is clear, use 'general'
        - When the comment expresses preference for a competitor, reflect this as negative sentiment
        - Be precise and objective in your analysis
        
        """
        
        try:
            start_time = time.time()
            logging.info(f"📤 Sending batch of {batch_size} comments to GPT-5-nano")
            
            response = await self.async_client.responses.parse(
                #model="gpt-4.1-nano-2025-04-14",
                model="gpt-5-nano-2025-08-07",
                reasoning={"effort": "minimal"},
                instructions=instructions,
                input=comments_text,
                text_format=BatchSentimentResponse,
            )
            
            end_time = time.time()
            duration = end_time - start_time
            logging.info(f"📥 Received response for batch of {batch_size} comments in {duration:.2f}s")
            
            # Convert batch results to individual analysis format
            results = []
            for analysis in response.output_parsed.analyses:
                comment_sentiment = _classify_from_percentage(analysis.sentiment)
                attribute_sentiment = _classify_from_percentage(analysis.attribute_sentiment)
                
                results.append({
                    "comment_id": analysis.comment_id,
                    "comment_sentiment": comment_sentiment,
                    "attribute_discussed": analysis.attribute_discussed,
                    "attribute_sentiment": attribute_sentiment,
                })
            
            return results
            
        except Exception as e:
            logging.error(f"❌ Failed to analyze comment batch: {e}")
            return []

    async def analyze_recent_comments(self, limit: int = 100) -> Dict[str, Any]:
        """Analyze up to 'limit' unanalyzed comments and update rows with results.

        Updates fields: comment_sentiment, attribute_discussed, attribute_sentiment.
        Only processes comments that haven't been analyzed yet.
        """
        settings = get_settings()
        
        result = db_service.get_unanalyzed_comments(limit=limit)
        comments = result.get("comments", [])

        if not comments:
            return {"updated": 0, "skipped": 0, "total_scanned": 0}

        # Extract product name from the first comment (all should be the same)
        product_name = comments[0].get("product_name")
        if not product_name:
            logging.warning("No product name found in comments")
            return {"updated": 0, "skipped": len(comments), "total_scanned": len(comments)}

        # Get product-specific attributes (cached after first call)
        logging.info(f"Getting attributes for product: {product_name}")
        attributes = self._get_product_attributes(product_name)

        # Split comments into batches
        batch_size = settings.ANALYSIS_BATCH_SIZE
        batches = [comments[i:i+batch_size] for i in range(0, len(comments), batch_size)]
        
        logging.info(f"🚀 Starting batch analysis: {len(comments)} comments → {len(batches)} batches of {batch_size}")

        async def process_batch(batch: List[Dict[str, Any]]) -> int:
            """Process a batch of comments with retry logic and fallback to individual processing."""
            try:
                # Try batch analysis first
                analyses = await self._analyze_comments_batch(batch, product_name, attributes)
                
                if not analyses:
                    logging.warning(f"⚠️ Batch analysis failed, falling back to individual processing for {len(batch)} comments")
                    return await self._process_individual_fallback(batch, product_name, attributes)
                
                # Update database for all comments in batch (single request)
                batch_updates = []
                for analysis in analyses:
                    batch_updates.append({
                        "id": analysis["comment_id"],
                        "comment_sentiment": analysis["comment_sentiment"],
                        "attribute_discussed": analysis["attribute_discussed"],
                        "attribute_sentiment": analysis["attribute_sentiment"],
                    })
                
                # Single batch database update
                successful_updates = await db_service.update_comments_batch_async(batch_updates)
                logging.info(f"✅ Batch completed: {successful_updates}/{len(analyses)} comments updated")
                
                return successful_updates
                
            except Exception as e:
                logging.error(f"❌ Failed processing batch: {e}")
                # Fallback to individual processing
                return await self._process_individual_fallback(batch, product_name, attributes)


        # Process all batches concurrently with rate limiting
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent batches
        
        async def process_batch_with_limit(batch: List[Dict[str, Any]], delay_s: float) -> int:
            """Process a batch with semaphore limiting and rate control."""
            await asyncio.sleep(delay_s)  # Stagger start times
            async with semaphore:  # Wait for available slot
                return await process_batch(batch)
        
        try:
            # Create tasks with staggered delays (1s apart)
            tasks = [
                process_batch_with_limit(batch, i * 1)
                for i, batch in enumerate(batches)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle any exceptions that occurred during processing
            updated = 0
            for result in results:
                if isinstance(result, Exception):
                    logging.error(f"Batch failed with exception: {result}")
                else:
                    updated += result
            
            skipped = len(comments) - updated
            logging.info(f"🎉 Analysis completed: {updated} updated, {skipped} skipped, {len(comments)} total")
            
        except Exception as e:
            logging.error(f"Critical error during analysis: {e}")
            return {"updated": 0, "skipped": len(comments), "total_scanned": len(comments)}

        return {"updated": updated, "skipped": skipped, "total_scanned": len(comments)}

    async def _process_individual_fallback(self, batch: List[Dict[str, Any]], product_name: str, attributes: List[str]) -> int:
        """Fallback to individual comment processing when batch fails."""
        logging.info(f"Processing {len(batch)} comments individually as fallback")
        
        async def process_individual(row: Dict[str, Any]) -> int:
            cid = row.get("id")
            text = (row.get("comment") or "").strip()
            if not cid or not text:
                return 0

            try:
                analysis = await self._analyze_comment(text, product_name, attributes)
                ok = await db_service.update_comment_fields_async(int(cid), analysis)
                return 1 if ok else 0
            except Exception as e:
                logging.error(f"Failed processing individual comment {cid}: {e}")
                return 0

        # Process all comments in the batch individually
        tasks = [process_individual(row) for row in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful_updates = 0
        for result in results:
            if isinstance(result, Exception):
                logging.error(f"Individual processing failed: {result}")
            else:
                successful_updates += result
        
        logging.info(f"Individual fallback completed: {successful_updates}/{len(batch)} comments updated")
        return successful_updates


# Global instance
analysis_service = AnalysisService()