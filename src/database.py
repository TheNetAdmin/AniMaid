from pathlib import Path
import json
import logging
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
                json.dump(self.data, f, indent=4,
                          default=self.encoder, ensure_ascii=False)

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
        else:
            raise Exception(f'Backend not supported: {self.backend.type}')

    def all(self) -> list:
        if self.backend.type == 'json':
            return self.backend.data
        else:
            raise Exception(f'Backend not supported: {self.backend.type}')
        return None

    def update(self, team, site='bangumi_moe', time=datetime.utcnow().isoformat()):
        if self.backend.type == 'json':
            for t in self.backend.data:
                if t['alias'] == team['alias']:
                    for s in t['source']:
                        if s['site'] == site:
                            s['last_update'] = time
        else:
            raise Exception(f'Backend not supported: {self.backend.type}')

class bangumi_moe_database(base_database):
    def __init__(self, config, secret):
        super().__init__(config, secret)
        self.site = bangumi_moe_site()
        self.logger = logging.getLogger('animaid.bangumi_moe_database')

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

    def search(self, torrent: dict) -> dict:
        tid = torrent['_id']
        if self.backend.type == 'json':
            for d in self.backend.data:
                if d['_id'] == tid:
                    return d
            return None
        else:
            raise Exception(f'Backend not supported: {self.backend.type}')

    def insert(self, torrent) -> bool:
        if self.search(torrent) is not None:
            return False
        if self.backend.type == 'json':
            self.backend.data.append(torrent)
        else:
            raise Exception(f'Backend not supported: {self.backend.type}')
        return True

    def update(self, team, max_pages=2, force=False):
        team = self.flat_team_info(team)
        update_interval = 2
        if 'update_interval' in team.keys():
            update_interval = team['update_interval']
        # Local logging function

        def log_info(msg: str, extra={}, default_extra={"team": team, "max_pages": max_pages, "force": force, "update_interval": update_interval}):
            self.logger.info(msg, extra={**default_extra, **extra})

        # Determine if we need to update database for this team
        need_update = True
        if parse_time(team['last_update']) + relative_time(update_interval) > datetime.utcnow():
            log_info(
                f'No need to update team [{team["alias"]:20}] from bangumi.moe, last update {team["last_update"]}')
            need_update = False
        if force and not need_update:
            log_info(f'Foce updating [{team["alias"]:20}]')
            need_update = True

        # Update
        if need_update:
            log_info(f'Updating [{team["alias"]:20}]')
            for p in range(max_pages):
                log_info(f'Page [{p}]', extra={'page': p})
                records = self.site.search_by_team(team, p)['torrents']
                for r in records:
                    succ = self.insert(r)
                    if not succ:
                        log_info(f'Found duplicated record (id: {r["_id"]}) on page {p}, stop here', extra={
                                 'record_id': r['_id'], 'page': p})
            # TODO: parse one more page to guarantee coverage
