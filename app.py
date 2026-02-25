from datetime import datetime, timedelta, date
from typing import Tuple, cast

from flask import Flask, render_template, request, Request
from indicate_data_exchange_client import AggregationPeriodKind

from providers import OpenAPIDataProvider

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


def special_times():
    today = date.today()
    return {
        "year_start":  today - timedelta(days=365),
        "month_start": today - timedelta(days=30),
        "week_start":  today - timedelta(days=7),
        "today":       today,
    }


def handle_time_parameters(request: Request) \
        -> Tuple[AggregationPeriodKind, date, date]:
    period = request.args.get('period', 'weekly')
    if period not in ['weekly', 'monthly', 'yearly']:
        raise RuntimeError(f'Bad period: {period}; must be weekly, monthly or yearly')
    period = cast(AggregationPeriodKind, period)

    today = date.today()
    default_end = today
    default_start = today - timedelta(days=29)

    start = cast(date, parse_date("start", default_start))
    end = cast(date, parse_date("end", default_end))

    return period, start, end


@app.route("/")
def overview():
    period, start, end = handle_time_parameters(request)
    indicators = DATA_PROVIDER.get_overview(period, start, end)
    return render_template("overview.html",
                           indicators=indicators,
                           period=period,
                           start=start,
                           end=end,
                           times=special_times())


@app.route("/indicator/<int:indicator_id>")
def indicator_detail(indicator_id):
    period, start, end = handle_time_parameters(request)
    detail = DATA_PROVIDER.get_indicator_detail(indicator_id, period, start, end)
    return render_template("detail.html",
                           detail=detail,
                           period=period,
                           start=start,
                           end=end,
                           times=special_times())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
