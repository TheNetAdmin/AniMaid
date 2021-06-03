import logging
from pathlib import Path

from plexapi.myplex import MyPlexAccount


class media_server:
    def __init__(self, config, secret):
        self.config = config
        self.secret = secret


class plex_server(media_server):
    def __init__(self, config, secret):
        super().__init__(config, secret)
        self.logger = logging.getLogger("animaid.plex_server")
        self.account = MyPlexAccount(
            secret["plex"]["username"], secret["plex"]["password"]
        )
        self.client = self.account.resource(secret["plex"]["server_name"]).connect()
        self.library = dict()
        for name, library in secret["plex"]["library_name"].items():
            self.library[name] = self.client.library.section(library)
        self.plex_ignore = secret["plex"]["ignore"]

    def _add_plex_ignore_recursive(self, path: Path):
        ignore_found = set()
        sub_dirs = []
        end_recursive = False
        for f in path.iterdir():
            if f.name == ".plexignore":
                return
            if f.name in self.plex_ignore:
                ignore_found.add(f)
            if f.is_dir():
                sub_dirs.append(f)
        if len(ignore_found) > 0:
            self.logger.info(
                f"Add a .plexignore file for [{ignore_found}] under {path}"
            )
            with open(path / ".plexignore", "w") as f:
                for ignore in ignore_found:
                    f.write(f"*{ignore.name}/*\n")
            end_recursive = True
        if end_recursive:
            return
        for d in sub_dirs:
            self._add_plex_ignore_recursive(d)

    def add_plex_ignore(self):
        for typ, sub_path in self.config["path"]["sub_path"].items():
            p = Path(self.config["path"]["target"]) / sub_path
            self.logger.info(f"Check and add .plexignore files under {p} recursively")
            self._add_plex_ignore_recursive(p)

    def update(self):
        for name, library in self.library.items():
            self.logger.info(f'Updating library for "{name}" type anima')
            library.update()
