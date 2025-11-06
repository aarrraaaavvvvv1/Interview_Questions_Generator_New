import os, time, requests
from typing import List, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlencode, urlparse as up, parse_qs
from config import SCRAPE_TIMEOUT, SCRAPE_TOP_K, SCRAPE_TRUNCATE_CHARS

class WebScraper:
    """Scrapes web content (Firecrawl if available, else HTML fallback) and auto-discovers sources."""

    def __init__(self, firecrawl_api_key: str = ""):
        self.firecrawl_api_key = (firecrawl_api_key or "").strip()
        self.session = requests.Session()
        self.timeout = SCRAPE_TIMEOUT
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; InterviewQGen/1.0; +https://example.com/bot)"
        }

    # ----------------------- Auto-Discovery -----------------------

    def _ddg_results(self, query: str, max_results: int = 5) -> List[str]:
        """
        Fetch top DuckDuckGo HTML results and return a list of destination URLs.
        Avoids API usage. Parses 'uddg' redirect links to original URLs.
        """
        try:
            params = {"q": query}
            url = f"https://duckduckgo.com/html/?{urlencode(params)}"
            r = self.session.get(url, timeout=self.timeout, headers=self.headers)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            urls: List[str] = []
            # DuckDuckGo html page has links like /l/?uddg=<encoded>
            for a in soup.select("a"):
                href = a.get("href") or ""
                if "/l/?" in href and "uddg=" in href:
                    qs = parse_qs(up(href).query)
                    if "uddg" in qs:
                        dest = qs["uddg"][0]
                        if dest.startswith("http"):
                            urls.append(dest)
                # Try direct links as backup:
                elif href.startswith("http"):
                    urls.append(href)
            # Deduplicate while preserving order
            seen = set()
            uniq = []
            for u in urls:
                d = self._domain(u)
                if (u not in seen) and d and d != "duckduckgo.com":
                    uniq.append(u)
                    seen.add(u)
            return uniq[:max_results]
        except Exception as e:
            print(f"DDG search error: {e}")
            return []

    def auto_discover_sources(self, query: str, max_sources: int = 3) -> List[Tuple[str, str]]:
        """
        Return [(url, 'discovered')] for top relevant sources discovered from the web.
        The second tuple entry is a label (not content). Content will be fetched in extract_many.
        """
        urls = self._ddg_results(query, max_results=max_sources * 2 or 5)
        # return (url, label) pairs; label is not used beyond debugging
        return [(u, "discovered") for u in urls[:max_sources]]

    # ----------------------- Extraction -----------------------

    def _clean_html(self, html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        texts = []
        for el in soup.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
            txt = el.get_text(" ", strip=True)
            if txt and len(txt.split()) > 2:
                texts.append(txt)
        cleaned = " ".join(" ".join(texts).split())
        return cleaned[:SCRAPE_TRUNCATE_CHARS]

    def _domain(self, url: str) -> str:
        try:
            return urlparse(url).netloc
        except Exception:
            return ""

    def extract_from_url(self, url: str) -> str:
        """
        Try Firecrawl (markdown) if available; fallback to GET + clean.
        """
        try:
            if self.firecrawl_api_key:
                endpoint = "https://api.firecrawl.dev/v1/scrape"
                headers = {
                    "Authorization": f"Bearer {self.firecrawl_api_key}",
                    "Content-Type": "application/json",
                }
                payload = {"url": url, "formats": ["markdown"]}
                r = self.session.post(endpoint, json=payload, headers=headers, timeout=self.timeout)
                if r.status_code == 200:
                    md = r.json().get("markdown", "")
                    if md:
                        return md[:SCRAPE_TRUNCATE_CHARS]

            # Fallback: raw HTML
            r = self.session.get(url, timeout=self.timeout, headers=self.headers)
            if r.status_code == 200:
                return self._clean_html(r.text)
        except Exception as e:
            print(f"URL extraction error: {e}")
        return ""

    def extract_many(self, urls: List[str], k: int = SCRAPE_TOP_K, pause: float = 0.7) -> List[Tuple[str, str]]:
        """Return list of (url, content) for up to k unique domains with good content."""
        results: List[Tuple[str, str]] = []
        seen_domains = set()
        for url in urls:
            if len(results) >= k:
                break
            dom = self._domain(url)
            if not dom or dom in seen_domains:
                continue
            content = self.extract_from_url(url)
            if content and len(content) > 200:
                results.append((url, content))
                seen_domains.add(dom)
            time.sleep(pause)
        return results
