import time
import re
import requests
from bs4 import BeautifulSoup

# Rotate through realistic User-Agent strings to reduce block rate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
    "Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]

_ua_index = 0

def _next_ua():
    global _ua_index
    ua = USER_AGENTS[_ua_index % len(USER_AGENTS)]
    _ua_index += 1
    return ua

def _get(url, params=None, headers=None, timeout=10):
    """Low-level GET with a rotating User-Agent. Returns a Response or None."""
    h = {"User-Agent": _next_ua(), "Accept-Language": "en-US,en;q=0.9"}
    if headers:
        h.update(headers)
    try:
        resp = requests.get(url, params=params, headers=h, timeout=timeout)
        resp.raise_for_status()
        return resp
    except requests.RequestException as e:
        print(f"  [ERROR] Request failed: {e}")
        return None


# ── 1. Google Search ─────────────────────────────────────────────────────────

def google_search(keywords, max_results=10):
    """
    Search Google for each keyword and return a list of result dicts.

    Each dict contains:
        keyword     : the query term used
        title       : page title
        url         : result URL
        description : snippet / meta description

    Args:
        keywords   (str | list): one keyword string or a list of them
        max_results (int)       : max results to collect per keyword

    Returns:
        list[dict]
    """
    if isinstance(keywords, str):
        keywords = [keywords]

    results = []

    for kw in keywords:
        print(f"[Google] Searching: '{kw}' …")
        query = kw.strip()
        start = 0
        collected = 0

        while collected < max_results:
            batch = min(10, max_results - collected)   # Google returns up to 10
            resp = _get(
                "https://www.google.com/search",
                params={"q": query, "num": batch, "start": start, "hl": "en"},
            )
            if resp is None:
                print(f"  [Google] Failed to fetch page, skipping '{kw}'")
                break

            soup = BeautifulSoup(resp.text, "lxml")

            # Google wraps organic results in <div class="g"> containers.
            # The inner structure varies; we look for the most stable anchors.
            found_in_page = 0
            for div in soup.select("div.g"):
                a_tag = div.select_one("a[href]")
                if not a_tag:
                    continue
                href = a_tag["href"]
                # Skip internal Google links
                if not href.startswith("http") or "google.com" in href:
                    continue

                title_tag = div.select_one("h3")
                title = title_tag.get_text(strip=True) if title_tag else ""

                # Description lives in various span/div combos across layouts
                desc = ""
                for sel in ["div.VwiC3b", "span.aCOpRe", "div[data-sncf]"]:
                    node = div.select_one(sel)
                    if node:
                        desc = node.get_text(separator=" ", strip=True)
                        break

                results.append({
                    "keyword":     kw,
                    "title":       title,
                    "url":         href,
                    "description": desc,
                })
                collected += 1
                found_in_page += 1
                if collected >= max_results:
                    break

            print(f"  [Google] Page starting at {start}: {found_in_page} results "
                  f"(total so far: {collected})")

            if found_in_page == 0:
                # No more results on this page
                break

            start += 10
            time.sleep(1)   # polite delay between paginated requests

        print(f"  [Google] Done '{kw}': {collected} results collected\n")
        time.sleep(1)   # delay between keywords

    return results


# ── 2. Reddit Search ─────────────────────────────────────────────────────────

REDDIT_SUBREDDITS = [
    "Christianity",
    "Bible",
    "Prayer",
    "Catholicism",
    "Christian",
]

def reddit_search(keywords, max_results=10):
    """
    Search Reddit's public JSON API across Christian-focused subreddits.
    No authentication required.

    Each dict contains:
        keyword      : the query term used
        subreddit    : subreddit name
        title        : post title
        author       : Reddit username
        profile_url  : full URL to the author's Reddit profile
        post_url     : full URL to the post

    Args:
        keywords   (str | list): one keyword string or a list of them
        max_results (int)       : max results to collect per keyword (across all subreddits)

    Returns:
        list[dict]
    """
    if isinstance(keywords, str):
        keywords = [keywords]

    results = []

    # Reddit's JSON API requires a descriptive User-Agent to avoid 429s
    reddit_headers = {
        "User-Agent": "zoe-leadgen/1.0 (lead generation research tool)",
    }

    for kw in keywords:
        print(f"[Reddit] Searching: '{kw}' …")
        collected = 0
        per_sub = max(1, max_results // len(REDDIT_SUBREDDITS))

        for sub in REDDIT_SUBREDDITS:
            if collected >= max_results:
                break

            limit = min(per_sub, max_results - collected, 25)  # Reddit max is 25 for public
            print(f"  [Reddit] r/{sub} …")

            resp = _get(
                f"https://www.reddit.com/r/{sub}/search.json",
                params={
                    "q":          kw,
                    "restrict_sr": "1",   # restrict to this subreddit
                    "sort":        "relevance",
                    "limit":       limit,
                    "t":           "all",
                },
                headers=reddit_headers,
            )

            if resp is None:
                print(f"  [Reddit] Failed to fetch r/{sub}, skipping")
                time.sleep(1)
                continue

            try:
                data = resp.json()
            except ValueError:
                print(f"  [Reddit] Invalid JSON from r/{sub}, skipping")
                time.sleep(1)
                continue

            posts = data.get("data", {}).get("children", [])
            found_in_sub = 0

            for post in posts:
                pd = post.get("data", {})
                author = pd.get("author", "")
                if not author or author in ("[deleted]", "AutoModerator"):
                    continue

                results.append({
                    "keyword":     kw,
                    "subreddit":   sub,
                    "title":       pd.get("title", ""),
                    "author":      author,
                    "profile_url": f"https://www.reddit.com/user/{author}",
                    "post_url":    f"https://www.reddit.com{pd.get('permalink', '')}",
                })
                collected += 1
                found_in_sub += 1
                if collected >= max_results:
                    break

            print(f"  [Reddit] r/{sub}: {found_in_sub} posts found")
            time.sleep(1)   # delay between subreddit requests

        print(f"  [Reddit] Done '{kw}': {collected} results collected\n")
        time.sleep(1)   # delay between keywords

    return results


# ── Quick smoke-test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Google test ===")
    g = google_search("Christian church outreach", max_results=5)
    for r in g:
        print(f"  {r['title'][:60]:60s}  {r['url'][:50]}")

    print("\n=== Reddit test ===")
    r = reddit_search("prayer request", max_results=5)
    for post in r:
        print(f"  [{post['subreddit']}] {post['title'][:50]:50s}  @{post['author']}")
