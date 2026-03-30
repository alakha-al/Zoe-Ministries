# mailer.py
# Handles sending outreach emails to leads.
# Functions:
#   - send_email(to, subject, body)     : sends a single email via SMTP
#   - send_bulk(lead_ids, template_key) : loops over a list of lead IDs and sends
#                                         personalised emails using a template
#   - load_template(template_key)       : loads an email template from /templates/email/
# SMTP credentials are read from config.py (never hardcoded here).
# Logs sent/failed status back to the database for tracking.
