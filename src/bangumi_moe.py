import requests
from dateutil.parser import parse as parse_time
from src.database import source_database
import re

def save_team(url: str, source_db):
    if url.startswith('https') and 'torrent' not in url:
        raise Exception(f'This is not a torrent url, as "torrent" is not part of the url. Click the anima title and use new page\'s url (should have "torrent" in it).')
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

    team = {
        "name": team_name,
        "source": [
            {
                "site": "bangumi_moe",
                "team_id": team_id,
                "last_update": parse_time('2000').isoformat()
            }
        ]
    }

    local_team = source_db.search_team(team)
    if local_team is not None:
        return local_team
    
    print(f'Please give this team a unique alias in English,')
    filename = response["content"][0][0]
    print(f'    filename: {filename}')
    auto_alias = re.findall(r'\[[\w\s-]+\]', filename)[0]
    if auto_alias:
        auto_alias = auto_alias.replace('[','').replace(']','').replace(' ', '_')
    team_alias = input(f'Input the team alias [{auto_alias}]:')
    team_alias = team_alias.strip()
    if len(team_alias) == 0:
        team_alias = auto_alias
    team['alias'] = team_alias

    # TODO: Check if alias is unique
    source_db.add_team(team)

    return team
