import os
import requests
from typing import List
import time

class WebScraper:
    """Scrapes web content using Firecrawl with fallback"""
    
    def __init__(self):
        self.firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY", "")
        self.firecrawl_base_url = "https://api.firecrawl.dev/v0"
        self.timeout = 15
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    
    def scrape_topic(self, topic: str, subtopics: List[str]) -> str:
        """Scrape web content for a topic using Firecrawl with fallback"""
        try:
            search_queries = [f"{topic} {st}" for st in subtopics] if subtopics else [topic]
            context_parts = []
            
            for query in search_queries[:3]:
                if self.firecrawl_api_key:
                    result = self._scrape_with_firecrawl(query)
                    if result:
                        context_parts.append(result)
                        continue
                
                result = self._scrape_with_fallback(query)
                if result:
                    context_parts.append(result)
            
            return " ".join(context_parts[:3]) if context_parts else ""
        
        except Exception as e:
            print(f"Web scraping error: {str(e)}")
            return ""
    
    def _scrape_with_firecrawl(self, query: str) -> str:
        """Scrape using Firecrawl API"""
        try:
            url = f"{self.firecrawl_base_url}/scrape"
            headers = {
                "Authorization": f"Bearer {self.firecrawl_api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "url": f"https://www.google.com/search?q={query.replace(' ', '+')}",
                "pageOptions": {
                    "onlyMainContent": True,
                    "excludeTags": ["nav", "footer", "script", "style"]
                }
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                content = data.get("markdown", "") or data.get("content", "")
                return content[:1000] if content else ""
        
        except Exception as e:
            print(f"Firecrawl error (falling back): {str(e)}")
        
        return ""
    
    def _scrape_with_fallback(self, query: str) -> str:
        """Fallback scraping using basic requests"""
        try:
            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            
            response = self.session.get(search_url, timeout=self.timeout)
            if response.status_code == 200:
                text = response.text
                snippets = []
                for line in text.split('\n'):
                    if len(line) > 50 and len(line) < 300:
                        if any(word in line.lower() for word in ['definition', 'meaning', 'tutorial', 'guide', 'example']):
                            snippets.append(line.strip()[:200])
                
                return " ".join(snippets[:2]) if snippets else ""
        
        except Exception as e:
            print(f"Fallback scraping error: {str(e)}")
        
        return ""
    
    def extract_text_from_url(self, url: str) -> str:
        """Extract text from a specific URL"""
        try:
            if self.firecrawl_api_key:
                headers = {
                    "Authorization": f"Bearer {self.firecrawl_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {"url": url}
                response = requests.post(
                    f"{self.firecrawl_base_url}/scrape",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    return response.json().get("markdown", "")[:1000]
            
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                return response.text[:1000]
        
        except:
            pass
        
        return ""
