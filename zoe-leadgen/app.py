import threading
from flask import Flask, render_template, request, jsonify
import scraper
import extractor

app = Flask(__name__)

WAIT_TIMES = {
    500:  "~10 minutes",
    1000: "~20 minutes",
    2000: "~40 minutes",
    5000: "~90 minutes",
}

# In-memory job store  { job_id: { status, leads, error } }
# (replaced by database.py in a later step)
_jobs = {}
_job_counter = 0
_jobs_lock = threading.Lock()


def _run_job(job_id, keywords, sources, max_results):
    """Background worker: scrape → extract → store results."""
    try:
        raw_results = []

        per_source = max(1, max_results // max(len(sources), 1))

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

            # Other sources (youtube, twitter, facebook, instagram,
            # church_dir, linkedin) will be wired in when their
            # scraper functions are added to scraper.py.

        print(f"\n[job {job_id}] Scraping done — {len(raw_results)} raw results")
        print(f"[job {job_id}] Extracting contact data …")

        leads = extractor.extract_leads(raw_results)

        with _jobs_lock:
            _jobs[job_id]["leads"]  = leads
            _jobs[job_id]["status"] = "done"

        print(f"[job {job_id}] Complete — {len(leads)} leads ready")

    except Exception as e:
        print(f"[job {job_id}] ERROR: {e}")
        with _jobs_lock:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"]  = str(e)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        global _job_counter

        keywords = request.form.getlist("keywords")
        sources  = request.form.getlist("sources")
        volume   = int(request.form.get("volume", 500))
        email    = request.form.get("email", "").strip()
        wait     = WAIT_TIMES.get(volume, "~10 minutes")

        # Default to google if nothing selected
        if not sources:
            sources = ["google"]

        # Create a job and start it in a background thread
        with _jobs_lock:
            _job_counter += 1
            job_id = _job_counter
            _jobs[job_id] = {"status": "running", "leads": [], "error": ""}

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
    """Polled by the confirmation page to check job progress."""
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        return jsonify({"status": "not_found", "count": 0})
    return jsonify({
        "status": job["status"],
        "count":  len(job["leads"]),
        "error":  job.get("error", ""),
    })


@app.route("/results/<int:job_id>")
def results(job_id):
    """Show the extracted leads for a completed job."""
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        return "Job not found", 404
    return render_template("results.html", leads=job["leads"], job_id=job_id)


if __name__ == "__main__":
    # Bound to 0.0.0.0 so it is reachable from the Windows browser via WSL IP
    app.run(host="0.0.0.0", port=5000, debug=False)
