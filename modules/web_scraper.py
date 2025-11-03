import os
import requests
from typing import List
import time

class WebScraper:
    """Scrapes web content using Firecrawl with automatic fallback - Your real-time knowledge base"""
    
    def __init__(self, firecrawl_api_key: str = ""):
        """
        Initialize WebScraper with optional Firecrawl API key
        
        Args:
            firecrawl_api_key: Optional Firecrawl API key for better scraping
        """
        self.firecrawl_api_key = firecrawl_api_key or os.getenv("FIRECRAWL_API_KEY", "")
        self.firecrawl_base_url = "https://api.firecrawl.dev/v0"
        self.timeout = 15
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_topic(self, topic: str, subtopics: List[str]) -> str:
        """
        Scrape web for current information on topic
        This acts as your dynamic, always-current knowledge base
        """
        try:
            # Build search queries
            search_queries = []
            if subtopics:
                for st in subtopics[:3]:  # Limit to 3 subtopics
                    search_queries.append(f"{topic} {st} tutorial latest")
            else:
                search_queries.append(f"{topic} interview questions latest trends")
            
            context_parts = []
            
            for query in search_queries:
                # Try Firecrawl first if API key available
                if self.firecrawl_api_key:
                    result = self._scrape_with_firecrawl(query)
                    if result:
                        context_parts.append(result)
                        continue
                
                # Fallback to basic scraping
                result = self._scrape_with_fallback(query)
                if result:
                    context_parts.append(result)
                
                # Add small delay between requests
                time.sleep(0.5)
            
            return " ".join(context_parts[:3]) if context_parts else ""
        
        except Exception as e:
            print(f"Web scraping error: {str(e)}")
            return ""
    
    def _scrape_with_firecrawl(self, query: str) -> str:
        """Use Firecrawl API for professional web scraping"""
        try:
            url = f"{self.firecrawl_base_url}/scrape"
            headers = {
                "Authorization": f"Bearer {self.firecrawl_api_key}",
                "Content-Type": "application/json"
            }
            
            # Search on multiple sources
            search_urls = [
                f"https://www.google.com/search?q={query.replace(' ', '+')}+site:medium.com",
                f"https://www.google.com/search?q={query.replace(' ', '+')}+site:stackoverflow.com",
                f"https://www.google.com/search?q={query.replace(' ', '+')}+tutorial"
            ]
            
            for search_url in search_urls[:1]:  # Try first source
                payload = {
                    "url": search_url,
                    "pageOptions": {
                        "onlyMainContent": True,
                        "excludeTags": ["nav", "footer", "script", "style", "aside"]
                    }
                }
                
                response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data.get("markdown", "") or data.get("content", "")
                    if content:
                        return content[:1500]  # Limit content length
        
        except Exception as e:
            print(f"Firecrawl error (using fallback): {str(e)}")
        
        return ""
    
    def _scrape_with_fallback(self, query: str) -> str:
        """Fallback scraping method using basic requests"""
        try:
            # Search multiple sources for diversity
            sources = [
                f"https://www.google.com/search?q={query.replace(' ', '+')}+latest",
                f"https://www.google.com/search?q={query.replace(' ', '+')}+tutorial",
                f"https://www.google.com/search?q={query.replace(' ', '+')}+best+practices"
            ]
            
            for search_url in sources[:1]:  # Use first source
                response = self.session.get(search_url, timeout=self.timeout)
                
                if response.status_code == 200:
                    text = response.text
                    
                    # Extract meaningful snippets
                    snippets = []
                    lines = text.split('\n')
                    
                    for line in lines:
                        # Look for content-rich lines
                        if 50 < len(line) < 300:
                            # Filter for relevant keywords
                            if any(keyword in line.lower() for keyword in [
                                'definition', 'meaning', 'tutorial', 'guide', 
                                'example', 'how to', 'best practice', 'interview'
                            ]):
                                cleaned = line.strip()
                                if cleaned and not cleaned.startswith('<'):
                                    snippets.append(cleaned[:250])
                    
                    if snippets:
                        return " ".join(snippets[:3])
        
        except Exception as e:
            print(f"Fallback scraping error: {str(e)}")
        
        return ""
    
    def extract_text_from_url(self, url: str) -> str:
        """Extract text from a specific URL"""
        try:
            # Try Firecrawl first
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
                    data = response.json()
                    return data.get("markdown", "")[:2000]
            
            # Fallback to direct request
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                return response.text[:2000]
        
        except Exception as e:
            print(f"URL extraction error: {str(e)}")
        
        return ""
