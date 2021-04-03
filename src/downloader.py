import qbittorrentapi as qbt
import logging
from typing import Dict, List


class downloader:
    def __init__(self, config, secret):
        self.config = config
        self.secret = secret

    def download(self, urls: list, path):
        pass

class qbittorrent(downloader):
    def __init__(self, config, secret):
        super().__init__(config, secret)
        self.logger = logging.getLogger('animaid.qbittorrent')
        self.logger.debug('Logging into qbittorrent')
        self.client = qbt.Client(host=self.secret['qbittorrent']['addr'],
                                 port=int(self.secret['qbittorrent']['port']),
                                 username=self.secret['qbittorrent']['username'],
                                 password=self.secret['qbittorrent']['password'])
        self.path = self.secret['qbittorrent']['download_path']

    def download(self, urls: list, path):
        save_path = self.path + '/' + path
        self.logger.info(f'Download to path {save_path}:')
        for url in urls:
            self.logger.info(f'    {url}')
        self.client.torrents_add(urls=urls, save_path=save_path)
    
    def get_all_info(self) -> dict:
        qbt_infos = self.client.torrents_info()
        all_info = dict()
        for info in qbt_infos:
            all_info[info.hash] = info
        return all_info
    
    def get_info(self, hashes: List[Dict]) -> dict:
        all_info = self.get_all_info()
        res = dict()
        for magnet_hash in hases:
            if magnet_hash in all_info.keys():
                res[magnet_hash] = all_info[magnet_hash]
        return res

def make_downloader_client(config, secret):
    if config['downloader'] == 'qbittorrent':
        return qbittorrent(config, secret)
    else:
        raise Exception(f'Unsupported downloader: {config["downloader"]}')