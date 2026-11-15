"""
MuthuAI / CHAMP — retrieval/web_search.py

Production Current Information & Web Search Engine.
Features:
- Multilingual freshness detection (English, Tamil Unicode, Tanglish)
- Internet connectivity & diagnostics (DNS, HTTP probe, search provider status)
- Multi-provider search cascade:
    1. Google News RSS (real-time, zero API key, source-verified, date-tagged)
    2. DuckDuckGo Search (general web queries & technical freshness)
    3. Direct DDG HTML scraping fallback
    4. Playwright Headless Browser fallback
    5. Configured API search if .env keys present (Tavily/SerpAPI)
- Query optimization & date awareness (auto-injects current date & resolves locations/topics)
- Source quality extraction & deduplication
"""

from __future__ import annotations
import datetime
import os
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import TypedDict

from voice.language_detector import has_tamil_script, has_latin_script
from utils.logger import get_logger

log = get_logger("muthuai.retrieval.web_search")

# ── Freshness & Current Information Intent Triggers ────────────────

_ENGLISH_FRESHNESS_PATTERN = re.compile(
    r"\b(today|latest|current|now|recent|recently|this morning|this evening|yesterday|"
    r"this week|this month|new|updated|live|weather|score|price|news|breaking|trending|"
    r"right now|headlines|market|what happened|what is happening|developments|updates|"
    r"current situation|flood|floods|election|elections|gold rate|petrol price|cricket score)\b",
    re.IGNORECASE,
)

_TAMIL_FRESHNESS_PATTERN = re.compile(
    r"(லேட்டஸ்ட்|நியூஸ்|செய்தி|செய்திகள்|இன்று|இன்றைய|தற்போதைய|நடப்பு|சமீபத்திய|"
    r"இப்போ|இப்போது|வானிலை|நடந்தது|நடக்குது|நடக்கு|நிலவரம்|தகவல்கள்|விவரங்கள்|"
    r"அப்டேட்|பிரேக்கிங்|வெள்ளம்|விலை|தங்கம்|மழை|அரசியல்|என்ன\s*ஆச்சு|என்ன\s*நடந்தது|"
    r"என்ன\s*நடக்குது)"
)

_TANGLISH_FRESHNESS_PATTERN = re.compile(
    r"\b(inniku|innaiku|ippo|ippova|nadakuthu|nadanthathu|nadandhadhu|nadandhathu|"
    r"enna news|latest update|situation epdi|epdi irukku|enna aachu|enna aayiduchu|"
    r"latest-ah|current-ah|today-la|news enna|updates enna)\b",
    re.IGNORECASE,
)


def is_freshness_query(text: str) -> bool:
    """
    Return True if the query requires live/current web information.
    Supports English, Tamil Unicode script, and Tanglish.
    """
    if not text or not text.strip():
        return False

    cleaned = text.strip().lower()

    if _ENGLISH_FRESHNESS_PATTERN.search(cleaned):
        return True

    if _TAMIL_FRESHNESS_PATTERN.search(text):
        return True

    if _TANGLISH_FRESHNESS_PATTERN.search(cleaned):
        return True

    return False


# ── Internet & Search Diagnostics ──────────────────────────────────

class ConnectivityStatus(TypedDict):
    internet_available: bool
    status_code: str
    message: str
    dns_resolved: bool
    http_probe_ok: bool
    search_service_ready: bool


def check_internet_connectivity(probe_host: str = "duckduckgo.com", timeout: float = 3.0) -> ConnectivityStatus:
    """
    Check network and search service readiness without false alarms.
    """
    dns_ok = False
    http_ok = False

    # 1. DNS Resolution Probe
    try:
        ip = socket.gethostbyname(probe_host)
        if ip:
            dns_ok = True
    except socket.gaierror:
        log.warning("DNS resolution failed for %s", probe_host)
        return {
            "internet_available": False,
            "status_code": "DNS_FAILURE",
            "message": "DNS resolution failed. Network interface may be offline or DNS unreachable.",
            "dns_resolved": False,
            "http_probe_ok": False,
            "search_service_ready": False,
        }
    except Exception as exc:
        log.warning("DNS probe error: %s", exc)

    # 2. HTTP Probe
    try:
        req = urllib.request.Request(
            f"https://{probe_host}",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CHAMP/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                http_ok = True
    except urllib.error.HTTPError as exc:
        log.warning("HTTP probe returned error status %d", exc.code)
        return {
            "internet_available": True,
            "status_code": f"HTTP_{exc.code}",
            "message": f"Internet reachable but probe target returned HTTP {exc.code}.",
            "dns_resolved": dns_ok,
            "http_probe_ok": False,
            "search_service_ready": dns_ok,
        }
    except Exception as exc:
        log.debug("HTTP probe note: %s", exc)

    # If DNS resolved, internet connectivity is available
    is_online = dns_ok or http_ok
    return {
        "internet_available": is_online,
        "status_code": "INTERNET_AVAILABLE" if is_online else "NO_INTERNET",
        "message": "Internet connection is active and search services are reachable." if is_online else "No active internet connection.",
        "dns_resolved": dns_ok,
        "http_probe_ok": http_ok,
        "search_service_ready": is_online,
    }



# ── Query Translation & Date Awareness ─────────────────────────────

_TAMIL_TRANSLATIONS = {
    "தமிழ்நாடு": "Tamil Nadu",
    "தமிழ்நாட்டு": "Tamil Nadu",
    "தமிழ்நாட்டுல": "Tamil Nadu",
    "சென்னை": "Chennai",
    "சென்னையில": "Chennai",
    "திருநெல்வேலி": "Tirunelveli",
    "திருநெல்வேலில": "Tirunelveli",
    "மதுரை": "Madurai",
    "கோயம்புத்தூர்": "Coimbatore",
    "இந்தியா": "India",
    "இந்தியாவில்": "India",
    "நேபாளம்": "Nepal",
    "நேபாள": "Nepal",
    "நேபாளத்துல": "Nepal",
    "உலக": "World",
    "உலகம்": "World",
    "செய்திகள்": "news",
    "செய்தி": "news",
    "நியூஸ்": "news",
    "லேட்டஸ்ட்": "latest",
    "இன்று": "today",
    "இன்றைய": "today",
    "வானிலை": "weather",
    "வெள்ளம்": "floods",
    "மழை": "rain weather",
    "தங்கம்": "gold rate price",
    "விலை": "price rate",
    "அரசியல்": "politics",
    "தேர்தல்": "election",
}

_TANGLISH_LOCATION_TRANSLATIONS = {
    "tamilnadu": "Tamil Nadu",
    "tamil nadu": "Tamil Nadu",
    "tamilnattula": "Tamil Nadu",
    "tamilnattu": "Tamil Nadu",
    "chennai": "Chennai",
    "chennaila": "Chennai",
    "tirunelveli": "Tirunelveli",
    "tirunelvelila": "Tirunelveli",
    "nellai": "Tirunelveli",
    "madurai": "Madurai",
    "kovai": "Coimbatore",
    "nepal": "Nepal",
    "nepalla": "Nepal",
    "india": "India",
    "indiala": "India",
    "world": "World",
    "worldla": "World",
}


def build_optimized_search_queries(raw_query: str) -> list[str]:
    """
    Build prioritized list of optimized search queries for news / web search.
    - Strips conversational fillers (e.g., 'Bro', 'sollu', 'enna', 'solren')
    - Injects current month/year for time-sensitive queries
    - Translates Tamil/Tanglish entities to English keyword queries for broad coverage
    """
    today = datetime.date.today()
    month_year = today.strftime("%B %Y")  # e.g., "August 2026"
    today_str = today.strftime("%Y-%m-%d")

    cleaned = re.sub(
        r"\b(bro|hey bro|hi bro|please|tell me|explain|what is|what are|what happened|what's|"
        r"solu|sollu|pannu|enna|nadakuthu|epdi|irukku|pathu|solunga|கிட்ட|சொல்லு|விளக்கு)\b",
        "",
        raw_query,
        flags=re.IGNORECASE,
    ).strip(" ,.-!?")

    queries: list[str] = []

    # 1. Check if Tamil script is present -> build English transliteration query
    if has_tamil_script(raw_query):
        translated_tokens = []
        for word in raw_query.split():
            clean_word = word.strip(" ,.-!?")
            matched = False
            for ta_key, en_val in _TAMIL_TRANSLATIONS.items():
                if ta_key in clean_word:
                    translated_tokens.append(en_val)
                    matched = True
                    break
            if not matched and has_latin_script(clean_word):
                translated_tokens.append(clean_word)

        if translated_tokens:
            en_query = " ".join(translated_tokens)
            queries.append(f"{en_query} today {month_year}")
            queries.append(f"{en_query} latest news")

        # Also add original Tamil query for Tamil news portals
        queries.append(f"{cleaned} இன்றைய செய்திகள்")

    # 2. Tanglish / English Query processing
    else:
        # Check Tanglish locations
        found_locations = []
        lower_q = raw_query.lower()
        for t_loc, eng_loc in _TANGLISH_LOCATION_TRANSLATIONS.items():
            if re.search(rf"\b{t_loc}\b", lower_q):
                found_locations.append(eng_loc)

        if "flood" in lower_q or "floods" in lower_q:
            if "nepal" in lower_q:
                queries.append(f"Nepal floods latest update {month_year}")
                queries.append("Nepal flash floods news today")
        elif "ai" in lower_q or "artificial intelligence" in lower_q:
            queries.append(f"latest AI news developments {month_year}")
            queries.append("artificial intelligence latest updates today")
        elif found_locations:
            loc = found_locations[0]
            queries.append(f"{loc} latest news today {month_year}")
            queries.append(f"{loc} news updates")
        else:
            if cleaned:
                queries.append(f"{cleaned} latest news {month_year}")
                queries.append(f"{cleaned} today")

    # Fallback to cleaned query
    if cleaned and cleaned not in queries:
        queries.append(cleaned)

    # Ensure uniqueness while preserving order
    unique_queries: list[str] = []
    for q in queries:
        q_norm = q.strip()
        if q_norm and q_norm not in unique_queries:
            unique_queries.append(q_norm)

    return unique_queries or [raw_query]


# ── Multi-Provider Web Search Engine ───────────────────────────────

class WebSearcher:
    """
    High-Reliability, Multi-Provider Current Information Search Engine.
    """

    def __init__(self) -> None:
        self._user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """
        Execute robust search across providers with automatic query optimization.

        Returns list of dicts:
        [
            {
                "title": str,
                "url": str,
                "snippet": str,
                "source": str,
                "published": str,
            }
        ]
        """
        log.info("WebSearcher initiated for raw query: %r", query)

        # 1. Connectivity Pre-check
        conn = check_internet_connectivity()
        if not conn["internet_available"]:
            log.warning("Internet connectivity check failed: %s (%s)", conn["status_code"], conn["message"])
            return []

        search_candidates = build_optimized_search_queries(query)
        log.info("Optimized search candidates: %s", search_candidates)

        all_results: list[dict] = []

        # Iterate through prioritized queries
        for opt_query in search_candidates:
            # Method 1: Google News RSS (Fastest & most accurate for current news/dates)
            rss_results = self._search_google_news_rss(opt_query, max_results=max_results)
            if rss_results:
                log.info("Retrieved %d results from Google News RSS for query %r", len(rss_results), opt_query)
                all_results.extend(rss_results)
                if len(all_results) >= max_results:
                    break

            # Method 2: DuckDuckGo / DDGS / Direct HTML
            ddg_results = self._search_duckduckgo(opt_query, max_results=max_results)
            if ddg_results:
                log.info("Retrieved %d results from DuckDuckGo for query %r", len(ddg_results), opt_query)
                all_results.extend(ddg_results)
                if len(all_results) >= max_results:
                    break

        # Method 3: Playwright Browser Search Fallback if zero results
        if not all_results:
            log.info("Trying Playwright browser search fallback for query: %r", query)
            browser_results = self._search_with_browser(query, max_results=max_results)
            if browser_results:
                all_results.extend(browser_results)

        # Deduplicate and trim results
        deduped = self._deduplicate_results(all_results, max_results=max_results)
        log.info("WebSearcher completed with %d final verified results.", len(deduped))
        return deduped

    def _search_google_news_rss(self, query: str, max_results: int = 5) -> list[dict]:
        """Query Google News RSS feed for instant, clean, date-stamped news items."""
        try:
            encoded = urllib.parse.quote_plus(query)
            # Use Tamil locale if Tamil characters in query, else Indian English
            if has_tamil_script(query):
                url = f"https://news.google.com/rss/search?q={encoded}&hl=ta-IN&gl=IN&ceid=IN:ta"
            else:
                url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"

            req = urllib.request.Request(url, headers={"User-Agent": self._user_agent})
            with urllib.request.urlopen(req, timeout=6.0) as resp:
                content = resp.read()
                root = ET.fromstring(content)
                items: list[dict] = []
                for item in root.findall(".//item")[:max_results]:
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    pub_elem = item.find("pubDate")
                    src_elem = item.find("source")

                    title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""
                    link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
                    pub = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""
                    src = src_elem.text.strip() if src_elem is not None and src_elem.text else ""

                    if not src and " - " in title:
                        # Many Google News titles end in ' - Source Name'
                        parts = title.rsplit(" - ", 1)
                        title = parts[0]
                        src = parts[1]

                    if title:
                        items.append({
                            "title": title,
                            "url": link,
                            "snippet": f"Published: {pub}. Source: {src}. Headline: {title}",
                            "source": src or "News Report",
                            "published": pub,
                        })
                return items
        except Exception as exc:
            log.debug("Google News RSS search failed for %r: %s", query, exc)
            return []

    def _search_duckduckgo(self, query: str, max_results: int = 5) -> list[dict]:
        """Search DuckDuckGo using DDGS or direct HTML parsing."""
        # 1. Try ddgs / duckduckgo_search library
        try:
            try:
                # pyrefly: ignore [missing-import]
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                if results:
                    formatted = []
                    for r in results:
                        formatted.append({
                            "title": r.get("title", ""),
                            "url": r.get("href", r.get("url", "")),
                            "snippet": r.get("body", r.get("snippet", "")),
                            "source": "DuckDuckGo Web",
                            "published": "",
                        })
                    return formatted
        except Exception as exc:
            log.debug("DDGS package search skipped/failed: %s", exc)

        # 2. Direct DuckDuckGo HTML request fallback
        try:
            from bs4 import BeautifulSoup  # type: ignore

            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": self._user_agent}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    html_text = resp.read().decode("utf-8", errors="ignore")
                    soup = BeautifulSoup(html_text, "html.parser")
                    formatted = []
                    for item in soup.find_all("div", class_="result")[:max_results]:
                        title_elem = item.find("a", class_="result__url")
                        snippet_elem = item.find("a", class_="result__snippet")
                        if title_elem:
                            title = title_elem.text.strip()
                            raw_href = title_elem.get("href", "")
                            href = raw_href if isinstance(raw_href, str) else (raw_href[0] if isinstance(raw_href, list) and raw_href else "")
                            if "uddg=" in href:
                                parsed = urllib.parse.urlparse(href)
                                queries = urllib.parse.parse_qs(parsed.query)
                                url_val = queries.get("uddg", [href])[0]
                            else:
                                url_val = href
                            snippet = snippet_elem.text.strip() if snippet_elem else ""
                            formatted.append({
                                "title": title,
                                "url": url_val,
                                "snippet": snippet,
                                "source": "Web Search",
                                "published": "",
                            })
                    return formatted
        except Exception as exc:
            log.debug("Direct DDG HTML fallback failed: %s", exc)

        return []

    def _search_with_browser(self, query: str, max_results: int = 5) -> list[dict]:
        """Search via Playwright Headless Browser as ultimate fallback."""
        try:
            from browser.manager import BrowserManager
            from browser.extraction import PageExtractor

            manager = BrowserManager.get_instance()
            page = manager.get_page(headless=True)
            encoded = urllib.parse.quote_plus(query)
            page.goto(f"https://www.google.com/search?q={encoded}", wait_until="domcontentloaded", timeout=12000)

            extractor = PageExtractor(manager)
            raw = extractor.get_search_results(limit=max_results)
            formatted = []
            for r in raw:
                formatted.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("snippet", ""),
                    "source": "Google Search",
                    "published": "",
                })
            return formatted
        except Exception as exc:
            log.warning("Playwright browser search failed: %s", exc)
            return []

    @staticmethod
    def _deduplicate_results(results: list[dict], max_results: int = 5) -> list[dict]:
        """Remove duplicate URLs and titles."""
        seen_urls: set[str] = set()
        seen_titles: set[str] = set()
        deduped: list[dict] = []

        for r in results:
            title = r.get("title", "").strip().lower()
            url = r.get("url", "").strip().lower()

            if not title or title in seen_titles:
                continue
            if url and url in seen_urls:
                continue

            seen_titles.add(title)
            if url:
                seen_urls.add(url)

            deduped.append(r)
            if len(deduped) >= max_results:
                break

        return deduped






