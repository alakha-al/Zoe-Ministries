# scheduler.py
# Manages recurring/background scraping jobs.
# Functions:
#   - start_scheduler()              : starts the APScheduler background scheduler
#   - schedule_job(keyword, location,
#                  interval_hours)   : adds a recurring scrape job to the scheduler
#   - remove_job(job_id)             : cancels a scheduled job by ID
#   - list_jobs()                    : returns all active scheduled jobs
# Uses APScheduler (BackgroundScheduler) so jobs run without blocking Flask.
# Job definitions are persisted in the SQLite DB so they survive app restarts.
