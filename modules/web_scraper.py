import requests
from bs4 import BeautifulSoup
from typing import List, Optional
import time

class WebScraper:
    """Scrapes web content for context enhancement"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        self.timeout = 10
    
    def scrape_topic(self, topic: str, subtopics: List[str]) -> str:
        try:
            search_query = f"{topic} {' '.join(subtopics)}"
            context_parts = []
            sources = [
                f"https://stackoverflow.com/search?q={search_query.replace(' ', '+')}",
                f"https://github.com/search?q={search_query.replace(' ', '+')}&type=code"
            ]
            for source in sources:
                try:
                    response = self.session.get(source, timeout=self.timeout)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        text_content = " ".join([p.get_text() for p in soup.find_all(['p', 'h1', 'h2', 'h3'])[:5]])
                        if text_content:
                            context_parts.append(text_content[:500])
                except:
                    continue
                time.sleep(1)
            return " ".join(context_parts[:2]) if context_parts else ""
        except:
            return ""
    
    def extract_text_from_url(self, url: str) -> str:
        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                return " ".join([p.get_text() for p in soup.find_all(['p', 'article', 'main'])])
            return ""
        except:
            return ""
