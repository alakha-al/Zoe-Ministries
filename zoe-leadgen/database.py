# database.py
# All SQLite database interactions using the built-in sqlite3 module.
# Functions:
#   - init_db()                   : creates tables if they don't exist
#   - insert_lead(lead_dict)      : inserts a new lead, skips duplicates
#   - get_all_leads(filters=None) : returns leads as list of dicts with optional filters
#   - update_lead(id, fields)     : updates fields on an existing lead record
#   - delete_lead(id)             : removes a lead by ID
#   - log_email_sent(lead_id)     : marks a lead as contacted with a timestamp
# Table: leads (id, name, address, phone, email, website, source, contacted, scraped_at)
