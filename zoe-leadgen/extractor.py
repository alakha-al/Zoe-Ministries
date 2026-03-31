import re
import time
import requests
from bs4 import BeautifulSoup

# ── Regex patterns ────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
)

_PHONE_RE = re.compile(
    r"(?:\+?\d[\d\s\-().]{6,}\d)"         # general international / local
)

_WHATSAPP_RE = re.compile(
    r"(?:whatsapp|wa\.me)[^\d+]*(\+?[\d\s\-]{7,15})",
    re.IGNORECASE,
)

_SOCIAL_PATTERNS = {
    "twitter":   re.compile(r"(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/([A-Za-z0-9_]{1,50})", re.IGNORECASE),
    "instagram": re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/([A-Za-z0-9_.]{1,50})", re.IGNORECASE),
    "facebook":  re.compile(r"(?:https?://)?(?:www\.)?facebook\.com/([A-Za-z0-9_.@\-]{1,100})", re.IGNORECASE),
    "linkedin":  re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|company)/([A-Za-z0-9_\-]{1,100})", re.IGNORECASE),
    "youtube":   re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/(?:channel/|user/|@)([A-Za-z0-9_\-]{1,100})", re.IGNORECASE),
}

# Countries / regions used for simple location detection in page text
_COUNTRY_HINTS = [
    "United States", "USA", "United Kingdom", "UK", "Canada", "Australia",
    "Nigeria", "Ghana", "Kenya", "South Africa", "India", "Philippines",
    "Jamaica", "Trinidad", "Barbados", "New Zealand", "Ireland",
]

# User-agent for page visits
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _fetch(url, timeout=10):
    """Fetch a URL and return (soup, raw_text) or (None, '') on failure."""
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        return soup, resp.text
    except Exception as e:
        print(f"  [extractor] Could not fetch {url}: {e}")
        return None, ""


def _clean(value):
    """Strip whitespace; return empty string instead of None."""
    return (value or "").strip()


# ── Field extractors ──────────────────────────────────────────────────────────

def extract_emails(text):
    """Return the first email found in text, or empty string."""
    matches = _EMAIL_RE.findall(text)
    # Filter out image/asset false-positives
    filtered = [m for m in matches if not re.search(r"\.(png|jpg|gif|svg|css|js)$", m, re.I)]
    return filtered[0] if filtered else ""


def extract_phones(text):
    """Return the first phone number found in text, or empty string."""
    matches = _PHONE_RE.findall(text)
    for m in matches:
        digits = re.sub(r"\D", "", m)
        if 7 <= len(digits) <= 15:
            return m.strip()
    return ""


def extract_whatsapp(text):
    """Return a WhatsApp number if explicitly mentioned, or empty string."""
    m = _WHATSAPP_RE.search(text)
    return _clean(m.group(1)) if m else ""


def extract_social_links(text):
    """
    Return a dict of social media profile URLs found in text.
    Keys: twitter, instagram, facebook, linkedin, youtube.
    Values: full URL string or empty string.
    """
    links = {}
    for platform, pattern in _SOCIAL_PATTERNS.items():
        m = pattern.search(text)
        if m:
            handle = m.group(1)
            # Reconstruct canonical URL
            bases = {
                "twitter":   "https://twitter.com/",
                "instagram": "https://instagram.com/",
                "facebook":  "https://facebook.com/",
                "linkedin":  "https://linkedin.com/in/",
                "youtube":   "https://youtube.com/@",
            }
            links[platform] = bases[platform] + handle
        else:
            links[platform] = ""
    return links


def extract_location(soup, text):
    """
    Try to find a country or city/state in the page.
    Checks <meta> tags first, then plain text hints.
    Returns a string or empty string.
    """
    if soup:
        # Some sites put geo info in meta tags
        for prop in ["geo.region", "geo.placename", "og:locale"]:
            tag = soup.find("meta", attrs={"name": prop}) or \
                  soup.find("meta", attrs={"property": prop})
            if tag and tag.get("content"):
                return _clean(tag["content"])

    for country in _COUNTRY_HINTS:
        if country.lower() in text.lower():
            return country
    return ""


def extract_name(soup):
    """
    Best-effort name extraction:
    og:title → <title> → first <h1>
    """
    if not soup:
        return ""
    # Open Graph title is usually the person/org name on profile pages
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        return _clean(og["content"])
    h1 = soup.find("h1")
    if h1:
        return _clean(h1.get_text())
    title = soup.find("title")
    if title:
        return _clean(title.get_text())
    return ""


# ── Main public function ──────────────────────────────────────────────────────

def extract_lead(raw_result):
    """
    Visit the URL in a scraper result dict and extract contact fields.

    Args:
        raw_result (dict): one item returned by scraper.google_search()
                           or scraper.reddit_search(). Must contain at
                           least one of: 'url', 'profile_url', 'post_url'.

    Returns:
        dict with keys:
            source, keyword, name, email, phone, whatsapp,
            location, website, twitter, instagram, facebook,
            linkedin, youtube, raw_title
    """
    # Decide which URL to visit
    url = (
        raw_result.get("profile_url")
        or raw_result.get("url")
        or raw_result.get("post_url")
        or ""
    )

    lead = {
        "source":    _clean(raw_result.get("source", raw_result.get("subreddit", ""))),
        "keyword":   _clean(raw_result.get("keyword", "")),
        "raw_title": _clean(raw_result.get("title", "")),
        "website":   _clean(url),
        "name":      "",
        "email":     "",
        "phone":     "",
        "whatsapp":  "",
        "location":  "",
        "twitter":   "",
        "instagram": "",
        "facebook":  "",
        "linkedin":  "",
        "youtube":   "",
    }

    if not url:
        return lead

    print(f"  [extractor] Visiting: {url[:80]}")
    soup, raw_text = _fetch(url)
    time.sleep(2)   # polite delay after every page visit

    if not soup:
        return lead

    # Extract all fields
    lead["name"]     = extract_name(soup)
    lead["email"]    = extract_emails(raw_text)
    lead["phone"]    = extract_phones(raw_text)
    lead["whatsapp"] = extract_whatsapp(raw_text)
    lead["location"] = extract_location(soup, raw_text)

    socials = extract_social_links(raw_text)
    lead.update(socials)

    print(f"    name={lead['name'][:30] or '—'}  "
          f"email={lead['email'] or '—'}  "
          f"phone={lead['phone'] or '—'}")

    return lead


def extract_leads(raw_results):
    """
    Process a list of scraper result dicts and return a list of lead dicts.

    Args:
        raw_results (list[dict]): output from scraper.google_search()
                                  or scraper.reddit_search()

    Returns:
        list[dict]
    """
    leads = []
    total = len(raw_results)
    for i, result in enumerate(raw_results, 1):
        print(f"[extractor] Processing {i}/{total} …")
        lead = extract_lead(result)
        leads.append(lead)
    print(f"[extractor] Complete — {total} leads processed.")
    return leads


# ── Smoke test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test with a single mock result (no live scrape needed)
    mock = [
        {
            "keyword":     "christian outreach",
            "title":       "Test page",
            "url":         "https://example.com",
            "description": "",
        }
    ]
    results = extract_leads(mock)
    for r in results:
        print(r)
