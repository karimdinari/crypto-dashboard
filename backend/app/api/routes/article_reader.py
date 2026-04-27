"""
Article Reader / Scraper
=========================
Fetches and extracts clean article content from news URLs.
Fixed: proper decompression, better bot-bypass headers, cloudscraper fallback.

pip install httpx readability-lxml beautifulsoup4 lxml cloudscraper
"""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# ── User agents ───────────────────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

# ── Source-specific CSS selectors ─────────────────────────────────────────────
SOURCE_SELECTORS: dict[str, dict] = {
    "cointelegraph.com": {
        "article": ".post-content, article .content, [class*='article__content'], .article-content",
        "title":   "h1.post__title, h1[class*='title'], h1",
        "author":  "[class*='author__name'], .post-meta__author, [class*='author']",
        "image": "figure.post-cover img, [class*='hero'] img",
    },
    "coindesk.com": {
        "article": "[class*='article-body'], .at-content-wrapper, main article, .article__content",
        "title":   "h1",
        "author":  "[class*='author-name'], [rel='author'], [class*='author']",
        "image":   "picture img, [class*='hero-image'] img, [class*='hero'] img",
    },
    "forexlive.com": {
        "article": ".article-content, .story-content, article .content, .post-body",
        "title":   "h1",
        "author":  ".author-name, .byline, [class*='author']",
        "image":   "article img:first-of-type",
    },
    "reuters.com": {
        "article": "[class*='article-body'], [class*='ArticleBody'], article",
        "title":   "h1",
        "author":  "[class*='author'], [rel='author']",
        "image":   "[class*='hero'] img, [class*='ArticleHero'] img",
    },
    "cnbc.com": {
        "article": ".ArticleBody-articleBody, [class*='article-body'], article",
        "title":   "h1",
        "author":  ".Author-authorName, [class*='author']",
        "image":   "[class*='hero'] img",
    },
}

# ── Response schema ───────────────────────────────────────────────────────────
class ArticleOut(BaseModel):
    url:        str
    title:      str
    author:     str
    source:     str
    image:      str | None
    content:    str
    text:       str
    word_count: int
    read_mins:  int
    success:    bool
    error:      str | None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _domain(url: str) -> str:
    return urlparse(url).netloc.replace("www.", "")


def _get_headers(url: str) -> dict[str, str]:
    import random
    domain = _domain(url)
    ua = random.choice(USER_AGENTS)
    return {
        "User-Agent":                ua,
        "Accept":                    "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language":           "en-US,en;q=0.9",
        # Do NOT set Accept-Encoding — let httpx handle decompression automatically
        "Referer":                   "https://www.google.com/",
        "DNT":                       "1",
        "Connection":                "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest":            "document",
        "Sec-Fetch-Mode":            "navigate",
        "Sec-Fetch-Site":            "cross-site",
        "Sec-CH-UA":                 '"Chromium";v="124", "Google Chrome";v="124"',
        "Sec-CH-UA-Mobile":          "?0",
        "Sec-CH-UA-Platform":        '"Windows"',
        "Cache-Control":             "no-cache",
        "Pragma":                    "no-cache",
    }


def _fetch_with_cloudscraper(url: str) -> str | None:
    """
    Fallback for Cloudflare-protected sites (e.g. Cointelegraph).
    cloudscraper bypasses Cloudflare's JS challenge automatically.
    pip install cloudscraper
    """
    try:
        import cloudscraper
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        r = scraper.get(url, timeout=20)
        if r.status_code == 200 and len(r.text) > 500:
            return r.text
    except ImportError:
        pass  # cloudscraper not installed, skip
    except Exception:
        pass
    return None


def _extract_with_selectors(soup: BeautifulSoup, url: str) -> dict:
    domain = _domain(url)
    sel    = next((v for k, v in SOURCE_SELECTORS.items() if k in domain), None)
    result: dict = {}
    if not sel:
        return result

    if t := soup.select_one(sel.get("title", "h1") or "h1"):
        result["title"] = t.get_text(strip=True)

    if a := soup.select_one(sel.get("author", "") or ""):
        result["author"] = a.get_text(strip=True)

    if img_el := soup.select_one(sel.get("image", "") or ""):
        src = (img_el.get("src") or img_el.get("data-src")
               or img_el.get("data-lazy-src") or img_el.get("data-original"))
        if src and src.startswith("http"):
            result["image"] = src

    if body := soup.select_one(sel.get("article", "") or ""):
        for tag in body.select(
            "script,style,.ad,.advertisement,[class*='related'],"
            "[class*='social'],nav,aside,.newsletter,[class*='subscribe'],"
            "[class*='promo'],[class*='sidebar'],[class*='share']"
        ):
            tag.decompose()
        result["content_html"] = str(body)
        result["text"]         = body.get_text(separator="\n", strip=True)

    return result


def _extract_with_readability(html: str) -> dict:
    try:
        from readability import Document
        doc     = Document(html)
        content = doc.summary()
        soup    = BeautifulSoup(content, "lxml")
        text    = soup.get_text(separator="\n", strip=True)
        return {"title": doc.title(), "content_html": content, "text": text}
    except Exception as e:
        return {"error": str(e)}


def _extract_meta(soup: BeautifulSoup) -> dict:
    meta: dict = {}
    for prop, key in [
        ("og:title",       "title"),
        ("og:description", "description"),
        ("og:image",       "image"),
    ]:
        el = soup.find("meta", property=prop)
        if el:
            meta[key] = el.get("content", "")

    author_el = soup.find("meta", {"name": "author"})
    if author_el:
        meta["author"] = author_el.get("content", "")

    return meta


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "iframe", "form", "button", "input", "svg", "noscript"]):
        tag.decompose()
    for p in soup.find_all("p"):
        if not p.get_text(strip=True):
            p.decompose()
    return str(soup)


def _is_garbage(text: str) -> bool:
    """Detect binary/garbled content that slipped through."""
    if not text:
        return True
    # Count non-printable / non-ASCII characters
    non_printable = sum(1 for c in text if ord(c) > 127 or (ord(c) < 32 and c not in '\n\r\t'))
    ratio = non_printable / max(len(text), 1)
    return ratio > 0.1  # more than 10% garbage = bad decode


# ── Main endpoint ─────────────────────────────────────────────────────────────
@router.get("/news/image")
async def proxy_image(url: str):
    """Proxy news images to bypass hotlink protection."""
    from fastapi.responses import StreamingResponse
    import httpx

    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        r = await client.get(url, headers={
            "User-Agent": USER_AGENTS[0],
            "Referer": f"https://{_domain(url)}/",
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        })
        return StreamingResponse(
            r.aiter_bytes(),
            media_type=r.headers.get("content-type", "image/jpeg"),
        )

@router.get("/news/article", response_model=ArticleOut)
async def fetch_article(url: str) -> ArticleOut:
    domain = _domain(url)
    html: str | None = None

    # ── Step 1: try httpx with proper headers ─────────────────────────────────
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=20.0,
            # httpx handles decompression automatically when no Accept-Encoding is forced
        ) as client:
            response = await client.get(url, headers=_get_headers(url))
            response.raise_for_status()

            # Force correct encoding
            raw_html = response.text

            if not _is_garbage(raw_html) and len(raw_html) > 500:
                html = raw_html
            else:
                # Try explicit encoding detection
                import chardet
                detected = chardet.detect(response.content)
                encoding = detected.get("encoding") or "utf-8"
                html = response.content.decode(encoding, errors="replace")

    except Exception as e:
        html = None

    # ── Step 2: fallback to cloudscraper (handles Cloudflare JS challenges) ───
    if not html or _is_garbage(html):
        html = _fetch_with_cloudscraper(url)

    if not html or _is_garbage(html):
        return ArticleOut(
            url=url, title="", author="", source=domain, image=None,
            content="", text="", word_count=0, read_mins=0,
            success=False,
            error="Could not fetch article — site may be behind Cloudflare or require JavaScript"
        )

    # ── Extract content ───────────────────────────────────────────────────────
    soup     = BeautifulSoup(html, "lxml")
    meta     = _extract_meta(soup)
    extracted = _extract_with_selectors(soup, url)

    # Fill missing fields with readability fallback
    if not extracted.get("content_html"):
        fallback = _extract_with_readability(html)
        for k, v in fallback.items():
            if k not in extracted:
                extracted[k] = v

    # Final values
    title   = extracted.get("title") or meta.get("title") or (soup.title.string if soup.title else "") or ""
    author  = extracted.get("author") or meta.get("author") or ""
    image   = extracted.get("image") or meta.get("image") or None
    content = _clean_html(extracted.get("content_html", ""))
    text    = extracted.get("text", "")

    if not text and content:
        text = BeautifulSoup(content, "lxml").get_text(separator="\n", strip=True)

    text       = re.sub(r"\n{3,}", "\n\n", text).strip()
    word_count = len(text.split())
    read_mins  = max(1, round(word_count / 200))

    return ArticleOut(
        url=url,
        title=str(title).strip(),
        author=str(author).strip(),
        source=domain,
        image=image if image and image.startswith("http") else None,
        content=content,
        text=text,
        word_count=word_count,
        read_mins=read_mins,
        success=bool(text and word_count > 20),
        error=None if (text and word_count > 20) else "Could not extract article content",
    )