import logging
from pathlib import Path

from log4mongo.handlers import MongoHandler

from .utils import chmkdir

mongo_handler = None

level_map = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}


def make_log_handler(config, secret):
    log_format = logging.Formatter(
        "[%(asctime)s][%(filename)20s:%(lineno)4s - %(funcName)20s() ][%(levelname)5s] %(message)s"
    )
    if config["backend"] == "file":
        Path(config["path"]).parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(filename=config["path"])
        handler.setFormatter(log_format)
    elif config["backend"] == "console":
        handler = logging.StreamHandler()
        handler.setFormatter(log_format)
    elif config["backend"] == "mongodb":
        ms = secret["mongodb"]
        handler = MongoHandler(
            host=ms["addr"],
            port=ms["port"],
            username=ms["username"],
            password=ms["password"],
            database_name=config["database"],
            collection=config["collection"],
        )
    return handler


def setup_log(config, secret):
    for log_type in ["default", "crash"]:
        if log_type == "default":
            logger = logging.getLogger()
        else:
            logger = logging.getLogger(f"animaid.{log_type}")

        logger.setLevel(logging.DEBUG)

        for handler_config in config[log_type]:
            handler = make_log_handler(handler_config, secret)
            if "level" in handler_config:
                level = level_map[handler_config["level"]]
            else:
                level = logging.INFO
            handler.setLevel(level)
            logger.addHandler(handler)
