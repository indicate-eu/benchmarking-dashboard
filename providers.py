import random
from datetime import timedelta

from indicate_data_exchange_client import DefaultApi, ApiClient, Configuration, AggregationPeriodKind


class DataProviderBase:
    def get_overview(self, period: AggregationPeriodKind, start_date, end_date):
        raise NotImplementedError()

    def get_indicator_detail(self, indicator_id, period: AggregationPeriodKind, start_date, end_date):
        raise NotImplementedError()


class RandomDataProvider(DataProviderBase):
    def __init__(self, num_hospitals=8, num_indicators=8, seed=42):
        self.num_hospitals = num_hospitals
        self.num_indicators = num_indicators
        self.seed = seed

    def _date_range(self, start, end):
        days = (end - start).days + 1
        for i in range(days):
            yield start + timedelta(days=i)

    def _rand_series(self, seed_base, start, end):
        r = random.Random(seed_base)
        series = []
        for d in self._date_range(start, end):
            # base value between 50 and 95
            base = r.uniform(50, 95)
            # add small day-to-day noise
            noise = r.uniform(-8, 8)
            val = max(0.0, min(100.0, base + noise))
            series.append((d, round(val, 1)))
        return series

    def get_overview(self, period: AggregationPeriodKind, start_date, end_date):
        indicators = []
        for iid in range(1, self.num_indicators + 1):
            name = f"Indicator {iid}"
            # each indicator has an 'all hospitals' average and 'own' hospital
            all_series = self._rand_series(seed_base=(self.seed + iid * 100), start=start_date, end=end_date)
            own_series = self._rand_series(seed_base=(self.seed + iid * 1000), start=start_date, end=end_date)

            avg_all = round(sum(v for _, v in all_series) / len(all_series)) if all_series else 0
            avg_own = round(sum(v for _, v in own_series) / len(own_series)) if own_series else 0

            num_patients = random.Random(self.seed + iid).randint(50, 1200)

            # simulate ranking among hospitals
            ranks = list(range(1, self.num_hospitals + 1))
            random.Random(self.seed + iid * 7).shuffle(ranks)
            rank = ranks[0]

            history = [{'date': d, 'value': v} for d, v in own_series]

            indicators.append({
                'id': iid,
                'name': name,
                'num_hospitals': self.num_hospitals,
                'num_patients': num_patients,
                'avg_own': avg_own,
                'avg_all': avg_all,
                'rank': f"{rank} / {self.num_hospitals}",
                'history': history,
            })

        return indicators

    def get_indicator_detail(self, indicator_id, period: AggregationPeriodKind, start_date, end_date):
        if indicator_id < 1 or indicator_id > self.num_indicators:
            return None

        name = f"Indicator {indicator_id}"
        description = f"Detailed description for {name}. This explains how adherence is computed and what it means."

        # For each hospital produce a row
        providers = []
        seeds = [self.seed + indicator_id * 100 + i for i in range(self.num_hospitals)]
        averages = []
        series_list = []
        for i, s in enumerate(seeds):
            ser = self._rand_series(seed_base=s, start=start_date, end=end_date)
            avg = round(sum(v for _, v in ser) / len(ser)) if ser else 0
            averages.append((i, avg))
            series_list.append(ser)

        # sort descending by average
        averages.sort(key=lambda x: x[1], reverse=True)

        # pick one index as 'own' hospital; let's choose the middle index
        own_index = self.num_hospitals // 2

        for rank_pos, (orig_idx, avg) in enumerate(averages, start=1):
            ser = series_list[orig_idx]
            label = "My Location" if orig_idx == own_index else "********"
            providers.append({
                'rank': rank_pos,
                'label': label,
                'num_patients': random.Random(self.seed + indicator_id * 13 + orig_idx).randint(10, 800),
                'avg': avg,
                'history': [{'date': d, 'value': v} for d, v in ser],
            })

        return {'id': indicator_id, 'name': name, 'description': description, 'providers': providers}


class OpenAPIDataProvider(DataProviderBase):
    def __init__(self, base_url):
        self.base_url = base_url
        self.api = DefaultApi(ApiClient(configuration=Configuration(host=base_url))) # TODO base_url

    def _get_indicators_info(self):
        return self.api.indicator_info_get()


    def get_overview(self, period: AggregationPeriodKind, start_date, end_date):
        # TODO: could cache this
        indicators_info = self._get_indicators_info()
        def find_indicator_info(indicator_id):
            return next((indicator_info for indicator_info in indicators_info
                         if indicator_info.concept_id == indicator_id),
                        None)
        #
        response = self.api.results_get(period, period_start=start_date, period_end=end_date)

        #
        indicator_results = {}
        def ensure_indicator(indicator_id):
            if indicator_id not in indicator_results:
                indicator_info = find_indicator_info(indicator_id)
                indicator_results[indicator_id] = {
                    'id':                 indicator_id,
                    'title':              indicator_info.title,
                    'providers':          set(),
                    'values':             [],
                    'observation_counts': [],
                    'history':            [],
                }
            return indicator_results[indicator_id]
        def add_to_history(history, observation):
            cell = next((cell for cell in history if cell['date'] == observation.aggregation_period_start), None)
            if cell is None:
                cell = {
                    'date':               quality_indicator_data.aggregation_period_start,
                    'values':             [],
                    'observation_counts': [],
                }
                history.append(cell)
            cell['values'].append(quality_indicator_data.average_value)
            cell['observation_counts'].append(quality_indicator_data.observation_count)

        for quality_indicator_data in response:
            indicator_result = ensure_indicator(quality_indicator_data.indicator_id)
            indicator_result['providers'] |= { quality_indicator_data.provider_id }
            add_to_history(indicator_result['history'], quality_indicator_data)
            indicator_result['values'].append(quality_indicator_data.average_value)
            indicator_result['observation_counts'].append(quality_indicator_data.observation_count)

        #
        def aggregate_history(history):
            return [
                {
                    "date": cell["date"].date(),
                    "value": sum(cell["values"]) / len(cell["values"]),
                    "observation_count": sum(cell["observation_counts"])
                }
                for cell in history
            ]
        def format_indicator_result(indicator_result):
            history = indicator_result['history']
            return {
                'id':            indicator_result['id'],
                'name':          indicator_result['title'],
                'num_hospitals': len(indicator_result['providers']),
                'num_patients':  sum(indicator_result['observation_counts']) / len(history),
                'avg_own':       0,
                'avg_all':       sum(indicator_result['values']) / len(history),
                'rank':          0,
                'history':       aggregate_history(history),
            }
        return [ format_indicator_result(indicator_result) for indicator_result in indicator_results.values() ]

    def get_indicator_detail(self, indicator_id, period: AggregationPeriodKind, start_date, end_date):
        indicators_info = self._get_indicators_info()
        # TODO: handle error
        indicator_info = next((info for info in indicators_info if info.concept_id == indicator_id), None)
        response = self.api.results_get(period, period_start=start_date, period_end=end_date)
        provider_results = {}

        def ensure_provider(provider_id):
            if provider_id not in provider_results:
                provider_results[provider_id] = {
                    'provider_id':        provider_id,
                    'history':            [],
                    'values':             [],
                    'observation_counts': [],
                }
            return provider_results[provider_id]

        for quality_indicator_data in response:
            if quality_indicator_data.indicator_id == indicator_id:
                provider_result = ensure_provider(quality_indicator_data.provider_id)
                provider_result['history'].append({
                    'date':              quality_indicator_data.aggregation_period_start.date(),
                    'value':             quality_indicator_data.average_value,
                    'observation_count': quality_indicator_data.observation_count
                })
                provider_result['values'].append(quality_indicator_data.average_value)
                provider_result['observation_counts'].append(quality_indicator_data.observation_count)
        #
        def format_provider_data(provider_result):
            is_self = provider_result['provider_id'] == 'e1bb92b8-0b84-11f1-9501-ee84309d5cdc'
            return {
                'is_self':      is_self,
                'rank':         0,
                'label':        '<Standort>' if is_self else '*' * 6,
                'num_patients': sum(provider_result['observation_counts']) / len(provider_result['observation_counts']),
                'avg':          sum(provider_result['values']) / len(provider_result['values']),
                'history':      provider_result['history'],
            }
        return {
            'id':          indicator_id,
            'name':        indicator_info.title,
            'description': indicator_info.description,
            'providers':   [ format_provider_data(provider_result)
                             for provider_result in provider_results.values()]
        }
