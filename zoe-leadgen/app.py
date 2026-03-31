import threading
import os
from flask import Flask, render_template, request, jsonify, send_file
import scraper
import extractor
import database
import excel_builder

app = Flask(__name__)

WAIT_TIMES = {
    500:  "~10 minutes",
    1000: "~20 minutes",
    2000: "~40 minutes",
    5000: "~90 minutes",
}

# Initialise SQLite tables on startup
database.init_db()


def _run_job(job_id, keywords, sources, max_results):
    """Background worker: scrape → extract → persist to DB."""
    try:
        raw_results = []
        per_source  = max(1, max_results // max(len(sources), 1))

        for source in sources:
            print(f"\n[job {job_id}] Scraping source: {source}")

            if source == "google":
                results = scraper.google_search(keywords, max_results=per_source)
                for r in results:
                    r["source"] = "google"
                raw_results.extend(results)

            elif source == "reddit":
                results = scraper.reddit_search(keywords, max_results=per_source)
                for r in results:
                    r["source"] = "reddit"
                raw_results.extend(results)

            # Additional sources (youtube, twitter, facebook, instagram,
            # church_dir, linkedin) wired in when scraper functions are added.

        print(f"\n[job {job_id}] {len(raw_results)} raw results — extracting …")
        leads = extractor.extract_leads(raw_results)

        # Persist every lead to SQLite
        saved = 0
        for lead in leads:
            row_id = database.insert_lead(lead, job_id=job_id)
            if row_id:
                saved += 1

        database.update_job(job_id, status="done", lead_count=saved)
        print(f"[job {job_id}] Done — {saved} leads saved to DB.")

    except Exception as e:
        print(f"[job {job_id}] ERROR: {e}")
        database.update_job(job_id, status="error", error=str(e))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        keywords = request.form.getlist("keywords")
        sources  = request.form.getlist("sources")
        volume   = int(request.form.get("volume", 500))
        email    = request.form.get("email", "").strip()
        wait     = WAIT_TIMES.get(volume, "~10 minutes")

        if not sources:
            sources = ["google"]

        # Create a DB-backed job record
        job_id = database.create_job(keywords, sources, volume, email)

        t = threading.Thread(
            target=_run_job,
            args=(job_id, keywords, sources, volume),
            daemon=True,
        )
        t.start()

        return render_template(
            "index.html",
            confirmed=True,
            email=email,
            volume=volume,
            wait=wait,
            keywords=keywords,
            sources=sources,
            job_id=job_id,
        )

    return render_template("index.html", confirmed=False)


@app.route("/status/<int:job_id>")
def job_status(job_id):
    """Polled every 4 s by the confirmation page."""
    job = database.get_job(job_id)
    if not job:
        return jsonify({"status": "not_found", "count": 0})
    return jsonify({
        "status": job["status"],
        "count":  job["lead_count"],
        "error":  job["error"],
    })


@app.route("/results/<int:job_id>")
def results(job_id):
    """Show extracted leads for a completed job."""
    job = database.get_job(job_id)
    if not job:
        return "Job not found", 404
    leads = database.get_leads_for_job(job_id)
    return render_template("results.html", leads=leads, job_id=job_id)


@app.route("/export/<int:job_id>")
def export(job_id):
    """Generate an Excel file and stream it as a download."""
    leads = database.get_leads_for_job(job_id)
    if not leads:
        return "No leads found for this job.", 404
    filepath = excel_builder.export_leads(leads, job_id=job_id)
    return send_file(
        filepath,
        as_attachment=True,
        download_name=os.path.basename(filepath),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.route("/all-leads")
def all_leads():
    """View all leads across every job."""
    leads = database.get_leads(limit=1000)
    return render_template("results.html", leads=leads, job_id=None)


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=False)
