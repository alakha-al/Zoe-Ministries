# config.py
# Central configuration — override sensitive values via environment variables.
#   - DB_PATH       : path to the SQLite database file (default: zoe-leadgen.db)
#   - SECRET_KEY    : Flask session secret key
#   - SMTP_HOST     : outgoing mail server hostname
#   - SMTP_PORT     : outgoing mail server port (default: 587)
#   - SMTP_USER     : email account username
#   - SMTP_PASSWORD : load from env, never hardcode
#   - MAIL_FROM     : sender address shown in outreach emails
#   - EXPORT_DIR    : directory where exported Excel files are saved
#   - DEBUG         : Flask debug mode flag (False in production)
