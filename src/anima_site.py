import requests
from dateutil.parser import parse as parse_time
import logging
import re


class site:
    def __init__(self):
        pass

    def parse_team(self, url: str) -> dict:
        pass


class bangumi_moe_site(site):
    def __init__(self):
        self.logger = logging.getLogger('animaid.bangumi_moe_site')

    def parse_team(self, url: str) -> dict:
        if url.startswith('https') and 'torrent' not in url:
            raise Exception(
                f'This is not a torrent url, as "torrent" is not part of the url. Click the anima title and use new page\'s url (should have "torrent" in it).')
        torrent_id = url.split('/')[-1]
        search_url = f'https://bangumi.moe/api/v2/torrent/{torrent_id}'
        response = requests.get(url=search_url).json()
        if 'team' not in response.keys() or '_id' not in response['team']:
            raise Exception(f'This record does not have a valid team info, '
                            f'try another anima record from the same team.')
        team_info = response['team']
        team_name = team_info['name']
        team_id = team_info['_id']

        print(f'The following team info is found:')
        print(f'    team name: {team_name}')
        print(f'    team id:   {team_id}')

        filename = response["content"][0][0]
        print(f'    filename: {filename}')
        auto_alias = re.findall(r'\[[\w\s-]+\]', filename)[0]
        if auto_alias:
            team_alias = auto_alias.replace(
                '[', '').replace(']', '').replace(' ', '_')
            print(f'    team alias:{team_alias}')
        else:
            print(f'Please give this team a unique alias in English,')
            team_alias = input(f'Input the team alias:')
            team_alias = team_alias.strip()

        team = {
            "_id": team_alias,
            "name": team_name,
            "alias": team_alias,
            "source": [
                {
                    "site": "bangumi_moe",
                    "team_id": team_id,
                    "last_update": parse_time('2000').isoformat()
                }
            ]
        }
        return team
    
    def _search(self, url,  ignore_properties=['introduction']):
        res = requests.get(url=url).json()
        res['torrents'] = sorted(res['torrents'], key=lambda x: parse_time(x['publish_time']), reverse=True)
        for t in res['torrents']:
            for i in ignore_properties:
                del t[i]
        if len(res) == 0:
            raise Exception(f'No data responded, something is wrong with the request to bangumi.moe, url: {url}', extra={'info':{'team': team, 'url': url}})
        return res

    def search_by_team(self, team, page, ignore_properties=['introduction']):
        url = f'https://bangumi.moe/api/v2/torrent/team/{team["team_id"]}?p={page+1}&LIMIT=500'
        return self._search(url, ignore_properties)
    
    def searcy_by_tag(self, tag, page, ignore_properties=['introduction']):
        url = f'https://bangumi.moe/api/v2/torrent/search?query=`{tag}`?p={page+1}&LIMIT=500'
        return self._search(url, ignore_properties)

    def search_by_torrent(self, torrent_id):
        url = f'https://bangumi.moe/api/v2/torrent/{torrent_id}'
        res = requests.get(url=url).json()
        if len(res) == 0:
            return None
        return res