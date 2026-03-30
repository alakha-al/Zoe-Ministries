# app.py
# Main Flask application entry point.
# Defines routes for the web UI:
#   - GET  /          : renders the index page with search form
#   - POST /search    : triggers a scrape job for the given keyword/location
#   - GET  /results   : displays leads stored in the database
#   - GET  /export    : triggers Excel export and returns the file download
#   - POST /send-mail : sends outreach emails to selected leads
# Initialises the database on startup and wires together all modules.
