# config.py
# Central configuration for the application.
# All sensitive values should be overridden via environment variables in production.
# Settings include:
#   - DB_PATH        : path to the SQLite database file (default: zoe-leadgen.db)
#   - SECRET_KEY     : Flask session secret key
#   - SMTP_HOST      : outgoing mail server hostname
#   - SMTP_PORT      : outgoing mail server port (default: 587)
#   - SMTP_USER      : email account username
#   - SMTP_PASSWORD  : email account password (load from env, never hardcode)
#   - MAIL_FROM      : sender address shown in outreach emails
#   - EXPORT_DIR     : directory where exported Excel files are saved
#   - DEBUG          : Flask debug mode flag (False in production)
