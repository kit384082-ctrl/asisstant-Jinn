import logging
from duckduckgo_search import DDGS
from typing import List, Dict

logger = logging.getLogger(__name__)

class WebSearcher:
    def __init__(self):
        self.ddgs = DDGS()

    def search(self, query: str, max_results: int = 3) -> List[Dict]:
        """Performs a web search using DuckDuckGo."""
        logger.info(f"Performing web search for: '{query}'")
        try:
            results = []
            for r in self.ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "href": r.get("href", ""),
                    "body": r.get("body", "")
                })
            return results
        except Exception as e:
            logger.error(f"Error during web search: {e}")
            return []
