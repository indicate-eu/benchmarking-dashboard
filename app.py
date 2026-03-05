import logging
from datetime import datetime, timedelta, date
from typing import Tuple, cast

from indicate_data_exchange_api_client import AggregationPeriodKind
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from configuration import load_configuration
from providers import OpenAPIDataProvider, RandomDataProvider


logger = logging.getLogger("uvicorn.error")


DATA_PROVIDER = None


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
    overview_data = DATA_PROVIDER.get_overview(period, start, end)
    context = {
        "period":           period,
        "start":            start,
        "end":              end,
        "times":            special_times(),
        'with_provider_id': overview_data['with_provider_id'],
        "indicators":       overview_data['indicators'],
    }
    return templates.TemplateResponse(request, 'overview.html', context=context)


async def indicator_detail(request: Request):
    indicator_id = request.path_params['indicator_id']
    period, start, end = handle_time_parameters(request)
    detail_data = DATA_PROVIDER.get_indicator_detail(indicator_id, period, start, end)
    context = {
        "period":           period,
        "start":            start,
        "end":              end,
        "times":            special_times(),
        'with_provider_id': detail_data['with_provider_id'],
        'name':             detail_data['name'],
        'description':      detail_data['description'],
        "providers":        detail_data['providers'],
    }
    return templates.TemplateResponse(request, 'detail.html', context=context)


# Load configuration and select data provider.
configuration = load_configuration()
if configuration.data_provider == 'dummy':
    DATA_PROVIDER = RandomDataProvider(num_hospitals=8, num_indicators=8)
elif configuration.data_provider == 'data-exchange-api':
    logger.info("Using backend '%s' with endpoint '%s'",
                configuration.data_provider,
                configuration.data_exchange_endpoint)
    if configuration.provider_id is None:
        logger.info("Provider id not set; running in \"hub mode\"")
    else:
        logger.info("Provider id '%s'", configuration.provider_id)
    DATA_PROVIDER = OpenAPIDataProvider(configuration.data_exchange_endpoint,
                                        configuration.provider_id)


app = Starlette(debug=configuration.debug_mode, routes=[
    Mount('/static', StaticFiles(directory='static'), name='static'),
    Route('/', overview),
    Route("/indicator/{indicator_id:int}", indicator_detail),
])
