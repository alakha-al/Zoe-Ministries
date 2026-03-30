# extractor.py
# Parses raw HTML and extracts structured lead data.
# Functions:
#   - extract_leads(html, source)  : parses a page and returns a list of lead dicts
#   - extract_emails(text)         : finds email addresses using regex
#   - extract_phones(text)         : finds phone numbers using regex
#   - extract_social_links(html)   : pulls LinkedIn, Facebook, Instagram URLs
# Each lead dict: name, address, phone, email, website, source, scraped_at
