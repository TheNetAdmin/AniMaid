import logging
from log4mongo.handlers import MongoHandler
from .utils import chmkdir
from pathlib import Path


def make_log_handler(config, secret):
    log_format = logging.Formatter(
        '[%(asctime)s][%(filename)20s:%(lineno)4s - %(funcName)20s() ] %(message)s')
    if config['backend'] == 'file':
        Path(config['path']).parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(filename=config['path'])
        handler.setFormatter(log_format)
    elif config['backend'] == 'console':
        handler = logging.StreamHandler()
        handler.setFormatter(log_format)
    elif config['backend'] == 'mongodb':
        ms = secret['mongodb']
        handler = MongoHandler(host=ms['addr'], port=ms['port'], username=ms['username'],
                               password=ms['password'], database_name=config['database'], collection=config['collection'])
    return handler


level_map = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}


def setup_log(config, secret):
    for log in ['default', 'crash']:
        if log == 'default':
            logger = logging.getLogger()
        else:
            logger = logging.getLogger(f'animaid.{log}')
        for handler_config in config[log]:
            handler = make_log_handler(handler_config, secret)
            logger.addHandler(handler)
            if 'level' in handler_config:
                level = level_map[handler_config['level']]
            else:
                level = logging.INFO
            logger.setLevel(level)
