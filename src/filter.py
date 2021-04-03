from dateutil.parser import parse as parse_time
from typing import Dict, List
from pathlib import Path

class base_filter:
    def __init__(self, config):
        if config['type'] not in ['include', 'exclude']:
            raise Exception(f'Unknown filter type: {config["type"]}')
        self.config = config

    def cond(self, target) -> bool:
        raise Exception('Need to be implemented')

    def apply(self, all_targets: list) -> list:
        res = []
        for target in all_targets:
            if self.config['type'] == 'include':
                if self.cond(target):
                    res.append(target)
            elif self.config['type'] == 'exclude':
                if not self.cond(target):
                    res.append(target)
        return res

class file_extension_filter(base_filter):
    def cond(self, target: Path) -> bool:
        if target.suffix in self.config['extension']:
            return True
        return False

class file_name_filter(base_filter):
    def cond(self, target: Path) -> bool:
        if target.name in self.config['filename']:
            return True
        return False


class record_word_filter(base_filter):    
    def cond(self, target: dict) -> bool:
        for word in self.config['word']:
            if word in target['title']:
                return True
        return False

class record_date_filter(base_filter):
    def cond(self, target: dict) -> bool:
        start_time = parse_time(self.config['date'][0])
        end_time = parse_time(self.config['date'][1])
        if start_time > end_time:
            raise Exception(f'Date filter with wrong date order: {self.config}')
        publish_time = parse_time(target['publish_time'])
        if start_time <= publish_time < end_time:
            return True
        return False

def _make_filter(config):
    if 'type' not in config.keys():
        raise Exception(f'Filter "type" not set for {config}')
    if len(config.keys()) > 2:
        raise Exception(f'Expect only 1 filter, but got {len(config.keys())} for {config}')
    if 'word' in config.keys():
        return record_word_filter(config)
    elif 'date' in config.keys():
        return record_date_filter(config)
    elif 'extension' in config.keys():
        return file_extension_filter(config)
    elif 'filename' in config.keys():
        return file_name_filter(config)
    else:
        raise Exception(f'Unknown filter: {config}')

def make_filter(config, predefined_filters=[]):
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