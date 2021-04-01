from pathlib import Path
import json
from datetime import datetime
from src.anima_site import bangumi_moe_site
from dateutil.parser import parse as parse_time
from dateutil.relativedelta import relativedelta as relative_time

class base_backend:
    def __init__(self, config, secret):
        self.config = config
        self.secret = secret
    
    def __del__(self):
        pass
    

class json_backend(base_backend):
    data = None

    def __init__(self, config, secret):
        super().__init__(config, secret)
        self.type = 'json'
        self.file = self.config['path']
        with open(self.file, 'r') as f:
            self.data = json.load(f)
    
    def __del__(self):
        if self.data is not None:
            with open(self.file, 'w') as f:
                json.dump(self.data, f, indent=4, default=self.encoder, ensure_ascii=False)
    
    def encoder(o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()


def make_backend(config, secret):
    backend = config['backend']
    if backend == 'json':
        return json_backend(config, secret)
    elif backend == 'mongodb':
        return mongodb_backend(config, secret)
    else:
        raise Exception(f'Unknown backend: {backend}')


class base_database():
    def __init__(self, config, secret):
        self.backend = make_backend(config, secret)
        

class source_database(base_database):
    def __init__(self, config, secret):
        super().__init__(config, secret)

    def search(self, team) -> dict:
        if self.backend.type == 'json':
            for entry in self.backend.data:
                for src in entry['source']:
                    if src['site'] == 'bangumi_moe' and src['team_id'] == team['source'][0]['team_id']:
                        return entry
        return None
    
    def insert(self, team):
        if self.search(team) is not None:
            pass
        if self.backend.type == 'json':
            self.backend.data.append(team)

    def all(self) -> list:
        if self.backend.type == 'json':
            return self.backend.data
        return None

class bangumi_moe_database(base_database):
    def __init__(self, config, secret):
        super().__init__(config, secret)
        self.site = bangumi_moe_site()
    
    def flat_team_info(self, team) -> dict:
        flat = dict()
        flat['name'] = team['name']
        flat['alias'] = team['alias']
        for source in team['source']:
            if source['site'] == 'bangumi_moe':
                for k, v in source.items():
                    flat[k] = v
        if 'last_update' not in flat.keys():
            raise Exception(f'Source "bangumi_moe" not found in team: {team}')
        return flat

    def update(self, team, page=2, force=False):
        need_update = False
        team = self.flat_team_info(team)
        update_interval = 2
        if 'update_interval' in team.keys():
            update_interval = team['update_interval']
        if parse_time(team['last_update']) + relative_time(update_interval) < datetime.utcnow():
            print(f'No need to update from bangumi.moe, last update {team["last_update"]}')
        if force and not need_update:
            print(f'Foce updating')
            need_update = True
