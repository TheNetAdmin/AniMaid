import click
import json
from pathlib import Path
from src.utils import working_directory, check_and_copy
from src.bangumi_moe import save_team
from src.database import source_database

def setup(args, config_path=None):
    # 1. Creating example config files if not exists
    # TODO: use curr_path relative to this python script
    curr_path = Path.cwd()
    if config_path is None:
        config_path = Path(args['config_file']).parent
    with working_directory(config_path):
        for filename in ['config.json', 'secret.json', 'rename.json', 'record.json']:
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
@click.option('-e', '--record', default='config/record.json', required=True, type=click.Path())
@click.pass_context
def animaid(ctx, config, secret, rename, record):
    ctx.ensure_object(dict)
    ctx.obj['config_file'] = Path(config)
    ctx.obj['secret_file'] = Path(secret)
    ctx.obj['rename_file'] = Path(rename)
    ctx.obj['record_file'] = Path(record)
    setup(ctx.obj)
    for file_type in ['config', 'secret', 'rename', 'record']:
        with open(ctx.obj[f'{file_type}_file']) as f:
            ctx.obj[file_type] = json.load(f)
    ctx.obj['data'] = {
        "source": source_database(ctx.obj['config']['data']['source'], secret)
    }

@animaid.command()
@click.pass_context
def install(ctx, config_path):
    print(f'Installing animaid')
    setup(ctx.obj)
    print(f'Installation done')


@animaid.command()
@click.option('-u', '--url', required=True)
@click.pass_context
def add_team(ctx, url):
    team = save_team(url, ctx.obj['data']['source'])
    print(f'Team record in "source" database: {team}')

if __name__ == '__main__':
    animaid()