from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for
from providers import RandomDataProvider, OpenAPIDataProvider

app = Flask(__name__)

# Configuration
DEBUG_MODE = True
DATA_PROVIDER = OpenAPIDataProvider("http://localhost:8080") # RandomDataProvider(num_hospitals=8, num_indicators=8)


def parse_date(qname, default):
    s = request.args.get(qname)
    if not s:
        return default
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return default


@app.route("/")
def overview():
    today = datetime.today().date()
    default_end = today
    default_start = today - timedelta(days=29)

    start = parse_date("start", default_start)
    end = parse_date("end", default_end)

    indicators = DATA_PROVIDER.get_overview(start, end)

    return render_template("overview.html", indicators=indicators, start=start, end=end)


@app.route("/indicator/<int:indicator_id>")
def indicator_detail(indicator_id):
    today = datetime.today().date()
    default_end = today
    default_start = today - timedelta(days=29)

    start = parse_date("start", default_start)
    end = parse_date("end", default_end)

    detail = DATA_PROVIDER.get_indicator_detail(indicator_id, start, end)

    if detail is None:
        return redirect(url_for("overview"))

    return render_template("detail.html", detail=detail, start=start, end=end)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
