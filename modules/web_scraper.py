import os, requests, time
from typing import List, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from config import SCRAPE_TIMEOUT, SCRAPE_TOP_K, SCRAPE_TRUNCATE_CHARS
class WebScraper:
    def __init__(self, firecrawl_api_key: str = ""):
        self.firecrawl_api_key = firecrawl_api_key or os.getenv("FIRECRAWL_API_KEY", "")
        self.session = requests.Session()
        self.timeout = SCRAPE_TIMEOUT
    def _clean_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script","style","noscript"]): tag.decompose()
        texts = []
        for el in soup.find_all(["h1","h2","h3","h4","p","li"]):
            txt = el.get_text(" ", strip=True)
            if txt and len(txt.split()) > 2:
                texts.append(txt)
        cleaned = " ".join(" ".join(texts).split())
        return cleaned[:SCRAPE_TRUNCATE_CHARS]
    def _domain(self, url: str) -> str:
        try: return urlparse(url).netloc
        except Exception: return ""
    def extract_from_url(self, url: str) -> str:
        try:
            if self.firecrawl_api_key:
                endpoint = "https://api.firecrawl.dev/v1/scrape"
                headers = {"Authorization": f"Bearer {self.firecrawl_api_key}", "Content-Type": "application/json"}
                payload = {"url": url, "formats": ["markdown"]}
                r = self.session.post(endpoint, json=payload, headers=headers, timeout=self.timeout)
                if r.status_code == 200:
                    md = r.json().get("markdown","")
                    if md: return md[:SCRAPE_TRUNCATE_CHARS]
            r = self.session.get(url, timeout=self.timeout)
            if r.status_code == 200:
                return self._clean_html(r.text)
        except Exception as e:
            print(f"URL extraction error: {e}")
        return ""
    def extract_many(self, urls: List[str], k: int = SCRAPE_TOP_K, pause: float = 0.8) -> List[Tuple[str,str]]:
        results, seen = [], set()
        for url in urls:
            if len(results) >= k: break
            dom = self._domain(url)
            if dom in seen: continue
            content = self.extract_from_url(url)
            if content and len(content) > 200:
                results.append((url, content)); seen.add(dom)
            time.sleep(pause)
        return results
