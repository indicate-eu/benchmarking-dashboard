from datetime import datetime, timedelta, date
from typing import Tuple, cast

from indicate_data_exchange_client import AggregationPeriodKind
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from providers import OpenAPIDataProvider

# Configuration
DEBUG_MODE = True
DATA_PROVIDER = OpenAPIDataProvider("http://localhost:8080") # RandomDataProvider(num_hospitals=8, num_indicators=8)


templates = Jinja2Templates('templates')


def parse_date(request: Request, qname, default):
    s = request.query_params.get(qname)
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
    period = request.query_params.get('period', 'weekly')
    if period not in ['weekly', 'monthly', 'yearly']:
        raise RuntimeError(f'Bad period: {period}; must be weekly, monthly or yearly')
    period = cast(AggregationPeriodKind, period)

    today = date.today()
    default_end = today
    default_start = today - timedelta(days=29)

    start = cast(date, parse_date(request, "start", default_start))
    end = cast(date, parse_date(request, "end", default_end))

    return period, start, end


async def overview(request):
    period, start, end = handle_time_parameters(request)
    indicators = DATA_PROVIDER.get_overview(period, start, end)
    context = {
        "indicators": indicators,
        "period": period,
        "start": start,
        "end": end,
        "times": special_times(),
    }
    return templates.TemplateResponse(request, 'overview.html', context=context)


async def indicator_detail(request: Request):
    indicator_id = request.path_params['indicator_id']
    period, start, end = handle_time_parameters(request)
    detail = DATA_PROVIDER.get_indicator_detail(indicator_id, period, start, end)
    context = {
        "detail": detail,
        "period": period,
        "start": start,
        "end": end,
        "times": special_times(),
    }
    return templates.TemplateResponse(request, 'detail.html', context=context)


app = Starlette(debug=True, routes=[
    Mount('/static', StaticFiles(directory='static'), name='static'),
    Route('/', overview),
    Route("/indicator/{indicator_id:int}", indicator_detail),
])