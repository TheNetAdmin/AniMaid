from .filter import make_filter
from .database import bangumi_moe_database, source_database
import re
from typing import Dict, List

def records_by_name(records: List[Dict], name_pattern: str, regex: bool) -> List[Dict]:
    result = []
    for r in records:
        if regex:
            if len(re.findall(name_pattern, r['title'])) > 0:
                result.append(r)
        else:
            if name_pattern in r['title']:
                result.append(r)
    return result

def get_follow_records(follow, bangumi_moe_db, source_db):
    # Setup filter
    global_filters = {}
    for name, filter_config in follow['filter'].items():
        global_filters[name] = make_filter(filter_config, [])
    
    result_records = []
    for track in follow['track']:
        # Setup filter
        track_filters = []
        track_filters.append(global_filters['default'])
        track_filters.append(global_filters[track['type']])
        if 'filter' in track:
            for f in track['filter']:
                tf = make_filter(f, global_filters)
                track_filters.append(tf)

        # Search records and apply filter
        team = source_db.search_by_name(track['team_name'])
        if team is None:
            raise Exception(f'This team is not found: {track["team_name"]}')
        track_records = bangumi_moe_db.search_by_team(team)
        for f in track_filters:
            track_records = f.apply(track_records)
    
        # Parse each follow rule
        for rule in track['follow']:
            # Match name
            if 'regex' not in rule.keys():
                rule['regex'] = False
            rule_records = records_by_name(track_records, rule['name'], rule['regex'])
            if 'filter' in rule.keys():
                for f in rule['filter']:
                    rf = make_filter(f, global_filters)
                    rule_records = rf.apply(rule_records)
            for r in rule_records:
                r['track_type'] = track['type']
                result_records.append(r)
    return result_records