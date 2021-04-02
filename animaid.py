import click
import json
import logging
import traceback
from pathlib import Path
from src.utils import working_directory, check_and_copy
from src.anima_site import bangumi_moe_site
from src.database import source_database, bangumi_moe_database, download_database
from src.log import setup_log
from src.follow import get_follow_records

def setup_config(args, config_path=None):
    # 1. Creating example config files if not exists
    # TODO: use curr_path relative to this python script
    curr_path = Path.cwd()
    if config_path is None:
        config_path = Path(args['config_file']).parent
    with working_directory(config_path):
        for filename in ['config.json', 'secret.json', 'rename.json', 'follow.json']:
            check_and_copy(curr_path / 'docs' / 'example' / filename, Path('.') / filename)
    # 2. Creating database if not exists
    with open(args['config_file'], 'r') as f:
        config = json.load(f)
    Path('data').mkdir(parents=True, exist_ok=True)
    for data in config['data']:
        data_config = config['data'][data]
        if data_config['backend'] == 'json' and not Path(data_config['path']).exists():
            with open(data_config['path'], 'w') as f:
                f.write('[]')



@click.group()
@click.option('-c', '--config', default='config/config.json', required=True, type=click.Path())
@click.option('-s', '--secret', default='config/secret.json', required=True, type=click.Path())
@click.option('-r', '--rename', default='config/rename.json', required=True, type=click.Path())
@click.option('-e', '--follow', default='config/follow.json', required=True, type=click.Path())
@click.pass_context
def animaid(ctx, config, secret, rename, follow):
    ctx.ensure_object(dict)
    ctx.obj['config_file'] = Path(config)
    ctx.obj['secret_file'] = Path(secret)
    ctx.obj['rename_file'] = Path(rename)
    ctx.obj['follow_file'] = Path(follow)
    # Setup directory and read config files
    setup_config(ctx.obj)
    for file_type in ['config', 'secret', 'rename', 'follow']:
        with open(ctx.obj[f'{file_type}_file']) as f:
            ctx.obj[file_type] = json.load(f)
    # Setup log
    setup_log(ctx.obj['config']['logging'], ctx.obj['secret'])
    ctx.obj['logger'] = logging.getLogger('animaid')
    # Read databases
    ctx.obj['data'] = {
        'source': source_database(ctx.obj['config']['data']['source'], secret),
        'download': download_database(ctx.obj['config']['data']['download'], secret),
        'bangumi_moe': bangumi_moe_database(ctx.obj['config']['data']['bangumi_moe'], secret)
    }

@animaid.command()
@click.pass_context
def install(ctx, config_path):
    print(f'Installing animaid')
    setup_config(ctx.obj)
    print(f'Installation done')


@animaid.command()
@click.option('-u', '--url', required=True)
@click.pass_context
def add_team(ctx, url):
    site = bangumi_moe_site()
    team = site.parse_team(url)
    source_db = ctx.obj['data']['source']
    source_db.insert(team)
    team = source_db.search(team)
    ctx.obj['logger'].info(f'Team record in source database: {team}')

@animaid.command()
@click.option('-t', '--anima_type', default='ongoing', required=True)
@click.option('-p', '--max_pages', default=2, required=True)
@click.option('-f', '--force', is_flag=True)
@click.pass_context
def update(ctx, anima_type, max_pages, force):
    if anima_type not in ['ongoing', 'bundle']:
        raise Exception(f"Unknown anima type: {anima_type}")
    # 1. Update teams' all recent records from bangumi.moe
    source_db = ctx.obj['data']['source']
    bangumi_moe_db = ctx.obj['data']['bangumi_moe']
    for team in source_db.all():
        bangumi_moe_db.update(team=team, max_pages=max_pages, force=force)
        source_db.update(team)
    # 2. Parse user-defined follow rules and find corresponding recent records
    records = get_follow_records(ctx.obj['follow'], bangumi_moe_db, source_db)
    download_db = ctx.obj['data']['download']
    for r in records:
        download_db.insert(r)
    # 3. Write discovered records to download database

@animaid.command()
@click.pass_context
def test(ctx):
    logger = logging.getLogger()
    logger.info("Test from animaid top module")
    logging.getLogger('animaid').info('Test animaid logger')
    raise Exception("Test exception")

if __name__ == '__main__':
    try:
        animaid()
    except Exception as e:
        logger = logging.getLogger('animaid.crash')
        logger.error(traceback.format_exc())
        logger.error(e)