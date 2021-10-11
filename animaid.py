import contextlib
import json
import logging
import traceback
from collections import defaultdict
from pathlib import Path

import click
from filelock import FileLock

from src.anima_site import bangumi_moe_site
from src.database import (bangumi_moe_database, download_database,
                          source_database)
from src.downloader import make_downloader_client
from src.follow import get_follow_records, get_notify_records
from src.log import setup_log
from src.media_server import plex_server
from src.organizer import organizer
from src.slack import slack_client
from src.utils import check_and_copy, chmkdir

global_slack = None


def setup_config(args, config_path=None):
    # 1. Creating example config files if not exists
    # TODO: use curr_path relative to this python script
    curr_path = Path.cwd()
    if config_path is None:
        config_path = Path(args["config_file"]).parent
    with chmkdir(config_path):
        for filename in ["config.json", "secret.json", "rename.json", "follow.json"]:
            check_and_copy(
                curr_path / "docs" / "example" / filename, Path(".") / filename
            )
    # 2. Creating database if not exists
    with open(args["config_file"], "r") as f:
        try:
            config = json.load(f)
        except json.decoder.JSONDecodeError as e:
            raise Exception(f"JSON file format error, file: {f}, error: {e.msg}")
    Path("data").mkdir(parents=True, exist_ok=True)
    for data in config["data"]:
        data_config = config["data"][data]
        if data_config["backend"] == "json" and not Path(data_config["path"]).exists():
            with open(data_config["path"], "w") as f:
                f.write("[]")


def check_dirs(ctx):
    # Checking download and media dirs
    config = ctx.obj["config"]
    for sub_path in config["path"]["sub_path"]:
        for parent in ["source", "target"]:
            p = Path(config["path"][parent]) / config["path"]["sub_path"][sub_path]
            p = p.resolve()
            if not p.exists() or not p.is_dir():
                raise Exception(
                    f"Dir not exists, please create it or point to a valid dir: {p}"
                )


def open_databases(ctx):
    ctx.obj["data"] = {
        "source": source_database(
            ctx.obj["config"]["data"]["source"], ctx.obj["secret"]
        ),
        "download": download_database(
            ctx.obj["config"]["data"]["download"], ctx.obj["secret"]
        ),
        "bangumi_moe": bangumi_moe_database(
            ctx.obj["config"]["data"]["bangumi_moe"], ctx.obj["secret"]
        ),
    }


def close_databases(ctx):
    for _, db in ctx.obj["data"].items():
        db.close()


@contextlib.contextmanager
def use_databases(ctx):
    lock = FileLock("data/animaid.lock", timeout=45)
    with lock:
        open_databases(ctx)
        try:
            yield
        finally:
            close_databases(ctx)


@click.group()
@click.option(
    "-c", "--config", default="config/config.json", required=True, type=click.Path()
)
@click.option(
    "-s", "--secret", default="config/secret.json", required=True, type=click.Path()
)
@click.option(
    "-r", "--rename", default="config/rename.json", required=True, type=click.Path()
)
@click.option(
    "-e", "--follow", default="config/follow.json", required=True, type=click.Path()
)
@click.pass_context
def animaid(ctx, config, secret, rename, follow):
    ctx.ensure_object(dict)
    ctx.obj["config_file"] = Path(config)
    ctx.obj["secret_file"] = Path(secret)
    ctx.obj["rename_file"] = Path(rename)
    ctx.obj["follow_file"] = Path(follow)
    # Setup directory and read config files
    setup_config(ctx.obj)
    for file_type in ["config", "secret", "rename", "follow"]:
        with open(ctx.obj[f"{file_type}_file"]) as f:
            try:
                ctx.obj[file_type] = json.load(f)
            except json.decoder.JSONDecodeError as e:
                raise Exception(f"JSON file format error, file: {f.name}, error: {e.msg}")

    # Setup log
    setup_log(ctx.obj["config"]["logging"], ctx.obj["secret"])
    ctx.obj["logger"] = logging.getLogger("animaid")

    # Check dirs
    check_dirs(ctx)

    # Setup slack
    if ctx.obj["config"]["slack"]:
        ctx.obj["slack"] = slack_client(ctx.obj["config"], ctx.obj["secret"])
        global global_slack
        global_slack = slack_client(ctx.obj["config"], ctx.obj["secret"])


@animaid.command()
@click.pass_context
def install(ctx, config_path):
    print(f"Installing animaid")
    setup_config(ctx.obj)
    print(f"Installation done")


@animaid.command()
@click.option("-u", "--url", help="URL of a team's anima", required=True)
@click.pass_context
def add_team(ctx, url):
    with use_databases(ctx):
        site = bangumi_moe_site()
        team = site.parse_team(url)
        source_db = ctx.obj["data"]["source"]
        source_db.insert(team)
        team = source_db.search(team)
        ctx.obj["logger"].info(f"Team record in source database: {team}")


@animaid.command()
@click.option("-f", "--force", is_flag=True)
@click.option("-a", "--apply_download", is_flag=True)
@click.option("-t", "--team_alias")
@click.option("-p", "--max_pages", default=2, required=True)
@click.pass_context
def update(ctx, max_pages, force, apply_download, team_alias):
    with use_databases(ctx):
        # 1. Update teams' all recent records from bangumi.moe
        ctx.obj["logger"].info("Update records from animation sites")
        source_db = ctx.obj["data"]["source"]
        bangumi_moe_db = ctx.obj["data"]["bangumi_moe"]
        if team_alias:
            teams_to_update = [source_db.search_by_name(team_alias)]
        else:
            teams_to_update = source_db.all()

        all_new_records = []
        for team in teams_to_update:
            records = bangumi_moe_db.update(team=team, max_pages=max_pages, force=force)
            all_new_records += records
            source_db.update(team)

        # 2. Parse user-defined follow rules and find corresponding recent records
        ctx.obj["logger"].info("Parse notify rules and notify in slack")
        notify_records = get_notify_records(ctx.obj['follow'], all_new_records, source_db)
        if len(notify_records) > 0:
            ctx.obj['slack'].notify_new_potential_records(notify_records)

        ctx.obj["logger"].info("Parse follow rules and find records")
        records = get_follow_records(ctx.obj["follow"], bangumi_moe_db, source_db)
        download_db = ctx.obj["data"]["download"]

        # 3. Write discovered records to download database
        for r in records:
            download_db.insert(r, apply_download)

        # 4. Update download states from downloader
        ctx.obj["logger"].info("Update download states from downloader")
        downloader = make_downloader_client(ctx.obj["config"], ctx.obj["secret"])
        download_db.update_states(downloader)


@animaid.command()
@click.pass_context
def download(ctx):
    with use_databases(ctx):
        # 1. Update download states from downloader
        ctx.obj["logger"].info("Parse download jobs")
        downloader = make_downloader_client(ctx.obj["config"], ctx.obj["secret"])
        download_db = ctx.obj["data"]["download"]
        download_db.update_states(downloader)
        # 2. Get all need download magnets
        all_need_download = download_db.get_need_download()
        jobs = defaultdict(list)
        for record in all_need_download:
            magnet_hash = record["magnet_hash"]
            track_type = record["track_type"]
            jobs[track_type].append(magnet_hash)
        for track_type, magnet_hashes in jobs.items():
            sub_path = ctx.obj["config"]["path"]["sub_path"][track_type]
            downloader.download(magnet_hashes, sub_path)
        ctx.obj["logger"].info(
            f"Done parsing download jobs, found {len(all_need_download)} new hash records"
        )
        if len(all_need_download) > 0:
            for r in all_need_download:
                ctx.obj["logger"].info(f'Downloading {r["title"]}')
            if ctx.obj["config"]["slack"]:
                ctx.obj["slack"].notify_new_records(all_need_download)


@animaid.command()
@click.option("-a", "--apply", is_flag=True)
@click.pass_context
def organize(ctx, apply):
    with use_databases(ctx):
        # 1. Update download states and check for on-going download jobs
        downloader = make_downloader_client(ctx.obj["config"], ctx.obj["secret"])
        download_db = ctx.obj["data"]["download"]
        download_db.update_states(downloader)
        all_downloading = download_db.get_downloading()
        if len(all_downloading) > 0:
            ctx.obj["logger"].info(
                f"There are {len(all_downloading)} jobs downloading, cannot organize until they finish",
                extra={
                    "info": {"all_downloading": [j["title"] for j in all_downloading]}
                },
            )
            return
        # 2. Recursively organizing sub pathes
        org = organizer(ctx.obj["rename"])
        cfg = ctx.obj["config"]
        any_file_moved = False
        for typ, sub_path in cfg["path"]["sub_path"].items():
            p = Path(cfg["path"]["source"]) / cfg["path"]["sub_path"][typ]
            ctx.obj["logger"].info(f'Organizing "{typ}" path: {p}')
            ctx.obj["logger"].info(f"Renaming")
            org.rename_recursive(p, apply)
            ctx.obj["logger"].info(f"Moving")
            src = p
            tgt = Path(cfg["path"]["target"]) / cfg["path"]["sub_path"][typ]
            moved = org.move_files(src, tgt, apply)
            any_file_moved = any_file_moved or moved
        # 3. Update PLEX
        if any_file_moved and ctx.obj["config"]["plex"]:
            plex = plex_server(ctx.obj["config"], ctx.obj["secret"])
            plex.add_plex_ignore()
            plex.update()
            ctx.obj["slack"].notify_organize()


@animaid.command()
@click.option("-t", "--team_alias")
@click.option("-n", "--anima_name")
@click.pass_context
def search_anima(ctx, team_alias, anima_name):
    with use_databases(ctx):
        bgm_db = ctx.obj["data"]["bangumi_moe"]
        result = bgm_db.search_anima(anima_name, team_alias)
        ctx.obj["logger"].info(f"Found {len(result)} records:")
        for i, r in enumerate(result):
            ctx.obj["logger"].info(f"    {i:02}: {r}")
        ctx.obj["logger"].info(f"Search anima operation finished")


@animaid.command()
@click.pass_context
def test(ctx):
    with use_databases(ctx):
        # 1. Update download states and check for on-going download jobs
        downloader = make_downloader_client(ctx.obj["config"], ctx.obj["secret"])
        download_db = ctx.obj["data"]["download"]
        # download_db.update_states(downloader)


if __name__ == "__main__":
    exit_code = 0
    try:
        animaid()
    except Exception as e:
        logger = logging.getLogger("animaid.crash")
        logger.error(traceback.format_exc())
        logger.error(e)
        if global_slack is not None:
            global_slack.notify_exception(e)
        exit_code = 1
    exit(exit_code)
