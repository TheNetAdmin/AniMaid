from pathlib import Path
import json

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


class source_database():
    def __init__(self, config, secret):
        self.backend = make_backend(config, secret)
    
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
