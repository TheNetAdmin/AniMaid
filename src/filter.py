from dateutil.parser import parse as parse_time
from typing import Dict, List

class base_record_filter:
    def __init__(self, config):
        if config['type'] not in ['include', 'exclude']:
            raise Exception(f'Unknown filter type: {config["type"]}')
        self.config = config

    def cond(self, record: dict) -> bool:
        raise Exception('Need to be implemented')

    def apply(self, all_records: List[Dict]) -> List[Dict]:
        res = []
        for record in all_records:
            if self.config['type'] == 'include':
                if self.cond(record):
                    res.append(record)
            elif self.config['type'] == 'exclude':
                if not self.cond(record):
                    res.append(record)
        return res

class word_filter(base_record_filter):    
    def cond(self, record: dict) -> bool:
        for word in self.config['word']:
            if word in record['title']:
                return True
        return False

class date_filter(base_record_filter):
    def cond(self, record: dict) -> bool:
        start_time = parse_time(self.config['date'][0])
        end_time = parse_time(self.config['date'][1])
        if start_time > end_time:
            raise Exception(f'Date filter with wrong date order: {self.config}')
        publish_time = parse_time(record['publish_time'])
        if start_time <= publish_time < end_time:
            return True
        return False

def _make_filter(config):
    if 'word' in config.keys() and 'date' in config.keys():
        raise Exception(f'Expect only one filter, but got two: {config}')
    if 'word' in config.keys():
        return word_filter(config)
    elif 'date' in config.keys():
        return date_filter(config)

def make_filter(config, predefined_filters):
    if isinstance(config, str):
        return predefined_filters[config]
    elif isinstance(config, dict):
        return _make_filter(config)
    elif isinstance(config, list):
        return record_filter_group(config)
    else:
        raise Exception(f'Unknow filter config: {config}')

class record_filter_group:
    def __init__(self, config):
        self.filters = []
        for filter_config in config:
            f = _make_filter(filter_config)
            self.filters.append(f)
    
    def apply(self, all_records: List[Dict]) -> List[Dict]:
        res = all_records
        for f in self.filters:
            res = f.apply(res)
        return res