# scraper.py
# Responsible for fetching raw HTML from target sources.
# Functions:
#   - scrape_google(keyword, location) : searches Google/Google Maps for businesses
#   - scrape_yelp(keyword, location)   : scrapes Yelp listings for the given query
#   - fetch_page(url)                  : low-level HTTP GET with retry logic and
#                                        rotating User-Agent headers
# Returns raw HTML strings to be processed by extractor.py.
# Uses requests + BeautifulSoup (or Selenium for JS-heavy pages).
