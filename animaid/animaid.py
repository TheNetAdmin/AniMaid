from inspect import Parameter
import prefect
from prefect import Parameter, Flow
import qbittorrent.qbittorrent as qbt

with Flow("qBittorrent") as flow:
    qbt_addr = Parameter("qbt_addr", default="localhost")
    qbt_port = Parameter("qbt_port", default=9001)
    qbt_user = Parameter("qbt_user", default="admin")
    qbt_pass = Parameter("qbt_pass", default="adminadmin")

    qbt_login = qbt.login(qbt_addr, qbt_port, qbt_user, qbt_pass)
    qbt_info = qbt.print_torrents_info(qbt_login, upstream_tasks= [qbt_login])

flow.run()
