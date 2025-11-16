"""FireCrawl web scraping integration"""

from firecrawl import Firecrawl
from config import FIRECRAWL_MAX_PAGES, FIRECRAWL_TIMEOUT
from typing import List, Dict

class FireCrawlService:
    """Service for web scraping using FireCrawl API"""
    
    def __init__(self, api_key: str):
        """Initialize FireCrawl with API key"""
        self.client = Firecrawl(api_key=api_key)
    
    def scrape_url(self, url: str) -> str:
        """Scrape a single URL and return markdown content"""
        try:
            result = self.client.scrape(
                url,
                formats=["markdown"],
                timeout=FIRECRAWL_TIMEOUT
            )
            return result.markdown if hasattr(result, 'markdown') else str(result)
        except Exception as e:
            raise Exception(f"Error scraping URL {url}: {str(e)}")
    
    def search_and_scrape(self, search_query: str, max_results: int = 3) -> List[Dict]:
        """Search the web and scrape top results"""
        try:
            # Use FireCrawl search feature
            results = []
            search_results = self.client.search(search_query)
            
            for i, result in enumerate(search_results[:max_results]):
                try:
                    content = self.scrape_url(result.get('url', ''))
                    results.append({
                        'url': result.get('url'),
                        'title': result.get('title'),
                        'content': content
                    })
                except:
                    continue
            
            return results
        except Exception as e:
            raise Exception(f"Error searching and scraping: {str(e)}")
