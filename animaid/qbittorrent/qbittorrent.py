import prefect
from prefect import task
import qbittorrentapi as qbt


@task
def login(addr: str, port: int, username: str, password: str) -> qbt.Client:
    logger = prefect.context.get("logger")
    client = qbt.Client(
        host=addr,
        port=port,
        username=username,
        password=password,
    )
    logger.info(f"qBittorrent version {client.app.version}")
    return client

@task
def print_torrents_info(client: qbt.Client):
    logger = prefect.context.get("logger")
    all_info = client.torrents_info()
    logger.info(all_info)
    return client