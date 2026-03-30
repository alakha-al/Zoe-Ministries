from flask import Flask, render_template, request

app = Flask(__name__)

WAIT_TIMES = {
    500:  "~10 minutes",
    1000: "~20 minutes",
    2000: "~40 minutes",
    5000: "~90 minutes",
}

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        keywords = request.form.getlist("keywords")
        sources  = request.form.getlist("sources")
        volume   = int(request.form.get("volume", 500))
        email    = request.form.get("email", "").strip()
        wait     = WAIT_TIMES.get(volume, "~10 minutes")
        return render_template(
            "index.html",
            confirmed=True,
            email=email,
            volume=volume,
            wait=wait,
            keywords=keywords,
            sources=sources,
        )
    return render_template("index.html", confirmed=False)


if __name__ == "__main__":
    # Bound to 0.0.0.0 so it is reachable from the Windows browser via WSL IP
    app.run(host="0.0.0.0", port=5000, debug=False)
