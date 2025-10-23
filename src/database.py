import copy
import json
import logging
from datetime import datetime
from pathlib import Path
from time import sleep
from typing import Dict, List

import pymongo as mongo
from dateutil.parser import parse as parse_time
from dateutil.relativedelta import relativedelta as relative_time
from filelock import FileLock
from pytz import UTC as utc

from src.anima_site import bangumi_moe_site


class base_backend:
    def __init__(self, config, secret):
        self.config = config
        self.secret = secret

    def close(self):
        pass


class json_backend(base_backend):
    data = None

    def __init__(self, config, secret):
        super().__init__(config, secret)
        self.type = "json"
        self.file = self.config["path"]
        self.lock = FileLock(self.file + ".lock", timeout=50)
        self.modified = False
        self.logger = logging.getLogger("animaid.database.json_backend")
        self.lock.acquire()
        with open(self.file, "r") as f:
            self.data = json.load(f)

    def close(self):
        if self.modified:
            self.logger.debug(f"Database {self.file} is modified, saving")
            with open(self.file, "w") as f:
                json.dump(
                    self.data, f, indent=4, default=self.encoder, ensure_ascii=False
                )
        else:
            self.logger.debug(f"Database {self.file} not modified, no need to save")
        self.lock.release()

    def insert(self, object):
        self.modified = True
        self.data.append(object)

    def update(self, index, new_object):
        self.modified = True
        self.data[index] = new_object

    def encoder(o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()


class mongodb_backend(base_backend):
    def __init__(self, config, secret):
        super().__init__(config, secret)
        self.type = "mongodb"
        self.database = self.config["database"]


def make_backend(config, secret):
    backend = config["backend"]
    if backend == "json":
        return json_backend(config, secret)
    elif backend == "mongodb":
        return mongodb_backend(config, secret)
    else:
        raise Exception(f"Unknown backend: {backend}")


class base_database:
    def __init__(self, config, secret):
        self.backend = make_backend(config, secret)

    def close(self):
        self.backend.close()


class download_database(base_database):
    def __init__(self, config, secret):
        super().__init__(config, secret)
        self.logger = logging.getLogger("animaid.download_database")

    def search(self, record: dict) -> dict:
        if self.backend.type == "json":
            for entry in self.backend.data:
                if 'record' not in entry or entry['record'] is None:
                    raise Exception(f"No 'record' found in this entry: {entry}")
                if "_id" not in entry["record"]:
                    raise Exception(f"Key '_id' not in: {entry['record']}, original entry: {entry}")
                if "_id" not in record:
                    raise Exception(f"Key '_id' not in {record}")
                if (
                    entry["record"]["site"] == "bangumi_moe"
                    and entry["record"]["_id"] == record["_id"]
                ):
                    return entry
        else:
            raise Exception(f"Backend not supported: {self.backend.type}")
        return None

    def insert(self, record: dict, apply=False):
        if self.search(record) is not None:
            return
        site = bangumi_moe_site()
        if self.backend.type == "json":
            download_record = {
                "downloader": "qbittorrent",
                "track_type": record["track_type"],
                "title": record["title"],
                "magnet": record["magnet"],
                "magnet_hash": record["infoHash"],
                "publish_time": record["publish_time"],
                "discover_time": datetime.utcnow().isoformat(),
                "download_status": "needDownload",
            }
            detailed_record = site.search_by_torrent(record["_id"])
            if detailed_record is not None:
                download_record["record"] = detailed_record
            else:
                download_record["record"] = {"_id": record["_id"]}
            download_record["record"]["site"] = "bangumi_moe"
            self.logger.info(
                f'Found new record: {record["title"]}',
                extra={"record": {"id": record["_id"], "title": record["title"]}},
            )
            if apply:
                self.backend.insert(download_record)
            else:
                self.logger.warning(
                    f'Record not inserted because "apply" is not set: {record["title"]}',
                    extra={"record": {"id": record["_id"], "title": record["title"]}},
                )
        else:
            raise Exception(f"Backend not supported: {self.backend.type}")

    def update_states(self, download_client):
        status = download_client.get_all_info()
        if self.backend.type == "json":
            for i, entry in enumerate(self.backend.data):
                magnet_hash = entry["magnet_hash"]
                if magnet_hash in status.keys():
                    s = status[magnet_hash].state
                    if s == entry["download_status"]:
                        continue
                    new_object = copy.deepcopy(entry)
                    new_object["download_status"] = s
                    self.backend.update(i, new_object)
                    if s == "error":
                        self.logger.error(
                            f'Download error for {entry["title"]}',
                            extra={"record": entry["record"]},
                        )
                    if "use-115" in status[magnet_hash].tags:
                        self.logger.warning(
                            f'Download stalled for {entry["title"]}, it should be moved to 115 for downloading',
                            extra={"record": entry["record"]},
                        )
                        entry["download_status"] = "download-stalled-use-115"
                else:
                    if entry["download_status"] != "needDownload":
                        entry["download_status"] = "unknown"
        else:
            raise Exception(f"Backend not supported: {self.backend.type}")

    def get_need_download(self):
        if self.backend.type == "json":
            return [
                r for r in self.backend.data if r["download_status"] in ["needDownload"]
            ]
        else:
            raise Exception(f"Backend not supported: {self.backend.type}")

    def get_downloading(self):
        if self.backend.type == "json":
            return [
                r
                for r in self.backend.data
                if r["download_status"] in ["downloading", "metaDL"]
            ]
        else:
            raise Exception(f"Backend not supported: {self.backend.type}")


class source_database(base_database):
    def search(self, team) -> dict:
        if self.backend.type == "json":
            for entry in self.backend.data:
                for src in entry["source"]:
                    if (
                        src["site"] == "bangumi_moe"
                        and src["team_id"] == team["source"][0]["team_id"]
                    ):
                        return entry
        else:
            raise Exception(f"Backend not supported: {self.backend.type}")
        return None

    def search_by_name(self, team_name) -> dict:
        if self.backend.type == "json":
            for entry in self.backend.data:
                if entry["name"] == team_name or entry["alias"] == team_name:
                    return entry
        else:
            raise Exception(f"Backend not supported: {self.backend.type}")
        return None

    def insert(self, team):
        if self.search(team) is not None:
            pass
        if self.backend.type == "json":
            self.backend.insert(team)
        else:
            raise Exception(f"Backend not supported: {self.backend.type}")

    def all(self) -> list:
        if self.backend.type == "json":
            return self.backend.data
        else:
            raise Exception(f"Backend not supported: {self.backend.type}")
        return None

    def update(self, team, site="bangumi_moe", time=datetime.utcnow().isoformat()):
        if self.backend.type == "json":
            for t in self.backend.data:
                if t["alias"] == team["alias"]:
                    for s in t["source"]:
                        if s["site"] == site:
                            s["last_update"] = time
                            # TODO: Add new class method to update field
                            #       Not explicitly set modified as True
                            self.backend.modified = True
        else:
            raise Exception(f"Backend not supported: {self.backend.type}")

    def match(self, team_name, record) -> bool:
        """Check if 'record' is from team with 'team_name'"""
        team = self.search_by_name(team_name)
        if team is None:
            raise Exception(f"Team [{team_name}] not found")
        for tinfo in team["source"]:
            if "team_id" in tinfo and tinfo["team_id"] == record["team_id"]:
                return True
            if "team_tag_id" in tinfo and tinfo["team_tag_id"] in record.get(
                "tag_ids", []
            ):
                return True
        return False


class bangumi_moe_database(base_database):
    def __init__(self, config, secret):
        super().__init__(config, secret)
        self.site = bangumi_moe_site()
        self.logger = logging.getLogger("animaid.bangumi_moe_database")

    def flat_team_info(self, team) -> dict:
        flat = dict()
        flat["name"] = team["name"]
        flat["alias"] = team["alias"]
        for source in team["source"]:
            if source["site"] == "bangumi_moe":
                for k, v in source.items():
                    flat[k] = v
        if "last_update" not in flat.keys():
            raise Exception(f'Source "bangumi_moe" not found in team: {team}')
        return flat

    def search(self, torrent: dict) -> dict:
        tid = torrent["_id"]
        if self.backend.type == "json":
            for d in self.backend.data:
                if d["_id"] == tid:
                    return d
            return None
        else:
            raise Exception(f"Backend not supported: {self.backend.type}")

    def search_anima(self, anima_name, team_alias=None) -> list:
        if self.backend.type == "json":
            anima_name = anima_name.lower()
            if team_alias is None:
                return [
                    d["title"]
                    for d in self.backend.data
                    if anima_name in d["title"].lower()
                ]
            else:
                team_alias = team_alias.lower()
                return [
                    d["title"]
                    for d in self.backend.data
                    if anima_name in d["title"].lower()
                    and team_alias in d["content"][0][0].lower()
                ]
        else:
            raise Exception(f"Backend not supported: {self.backend.type}")

    def insert(self, torrent) -> bool:
        if self.search(torrent) is not None:
            return False
        if self.backend.type == "json":
            t = copy.deepcopy(torrent)
            del t["introduction"]
            self.backend.insert(t)
        else:
            raise Exception(f"Backend not supported: {self.backend.type}")
        return True

    def update(self, team, max_pages=2, force=False) -> list:
        team = self.flat_team_info(team)
        update_interval = 2
        if "update_interval" in team.keys():
            update_interval = team["update_interval"]
        # Local logging function

        def log_info(
            msg: str,
            extra={},
            default_extra={
                "info": {
                    "team": team,
                    "max_pages": max_pages,
                    "force": force,
                    "update_interval": update_interval,
                }
            },
        ):
            self.logger.info(msg, extra={**default_extra, **extra})

        # Determine if we need to update database for this team
        need_update = True
        if (
            parse_time(team["last_update"]) + relative_time(hours=update_interval)
            > datetime.utcnow()
        ):
            log_info(
                f'No need to update team [{team["alias"]:20}] from bangumi.moe, last update {team["last_update"]}'
            )
            need_update = False
        if force and not need_update:
            log_info(f'Foce updating [{team["alias"]:20}]')
            need_update = True

        # Update
        all_records = []
        if need_update:
            log_info(f'Updating [{team["alias"]:20}]')
            cnt_new_records = 0
            for p in range(max_pages):
                sleep(3)
                log_info(f"Page [{p}]")
                records = self.site.search_by_team(team, p, [])["torrents"]
                if "team_tag_id" in team:
                    log_info(f"Page `Search` [{p}]")
                    records += self.site.searcy_by_tag(team["team_tag_id"], p)[
                        "torrents"
                    ]
                stop = False

                for r in records:
                    succ = self.insert(r)
                    if succ:
                        cnt_new_records += 1
                        all_records.append(r)
                    else:
                        if not force:
                            log_info(
                                f'Found duplicated record (id: {r["_id"]}) on page {p}, stop here',
                                extra={"record": {"id": r["_id"], "title": r["title"]}},
                            )
                            stop = True
                            break
                        else:
                            all_records.append(r)
                            stop = False
                if stop:
                    break
            log_info(f"Inserted {cnt_new_records} new records to bangumi_moe database")
            # TODO: parse one more page to guarantee coverage

        return all_records

    def search_by_team(self, team) -> List[Dict]:
        team = self.flat_team_info(team)
        tid = team["team_id"]
        if self.backend.type == "json":
            res = []
            for t in self.backend.data:
                if "team" in t.keys() and t["team"]["_id"] == tid:
                    res.append(t)
                if "team_tag_id" in team:
                    if "tag_ids" in t.keys():
                        for tag_id in t["tag_ids"]:
                            if tag_id == team["team_tag_id"] and t not in res:
                                res.append(t)
            return res
        else:
            raise Exception(f"Backend not supported: {self.backend.type}")
