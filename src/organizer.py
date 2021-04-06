from .filter import make_filter
from pathlib import Path
import logging
import re
from collections import Counter
import copy
from .utils import chdir, chmkdir


class renamer:
    def __init__(self, rule):
        self.rule = rule
        self.desc = rule['description']
        self.type = rule['type']
        self.regex = rule['regex']
        self.file = rule['file']
        self.entries = []
        self.logger = logging.getLogger(
            f'animaid.renamer.{"_".join(self.desc.split(" "))}')
        if self.type in ['remove', 'check']:
            for e in rule['entries']:
                prefix = rule['prefix'] if 'prefix' in rule.keys() else ''
                suffix = rule['suffix'] if 'suffix' in rule.keys() else ''
                self.entries.append(prefix + e + suffix)
        else:
            self.entries = rule['entries']

    def apply(self, target: Path, typ) -> (Path, bool):
        # Check file type
        if self.file == 'dir' and typ == 'file':
            return target, False
        if self.file == 'file' and typ == 'dir':
            return target, False

        # Apply rules
        parent = target.parent
        name = target.name
        if self.type == 'transform':
            for e in self.entries:
                if self.regex:
                    name = re.sub(e['source'], e['target'], name)
                else:
                    name = name.replace(e['source'], e['target'])
        elif self.type == 'add_parent':
            for e in self.entries:
                if self.regex:
                    new_parent = re.sub(e['source'], e['target'], name)
                else:
                    new_parent = name.replace(e['source'], e['target'])
                name = Path(new_parent) / name
        elif self.type == 'remove':
            for e in self.entries:
                if self.regex:
                    name = re.sub(e, '', name)
                else:
                    name = name.replace(e, '')
        elif self.type == 'check':
            for e in self.entries:
                if self.regex:
                    if len(re.findall(e, name)) > 0:
                        raise Exception(
                            f'Renaming not clean, according to regex rule {e}, |{re.findall(e, name)[0]}| in |{name}|')
                else:
                    if e in name:
                        raise Exception(
                            f'Renaming not clean, according to rule {e}, |{e}| in |{name}|')
        return parent / name, True


class organizer:
    def __init__(self, config):
        self.config = config
        self.filters = {}
        self.logger = logging.getLogger('animaid.organizer')
        # Make filters
        for name, filter_config in config['filter'].items():
            self.filters[name] = make_filter(filter_config)
        # Make renamers
        self.renamers = []
        for rename_rule in config['rename_rule']:
            self.renamers.append(renamer(rename_rule))
        # Make movers
        self.movers = []
        for move_rule in config['move_rule']:
            self.movers.append(renamer(move_rule))

    def rename_single(self, target: Path) -> Path:
        for r in self.renamers:
            target = r.apply(target)
        return target

    def filter_files(self, source: Path) -> dict:
        source_files = {'dir': [], 'file': []}
        for f in source.iterdir():
            if f.is_dir():
                source_files['dir'].append(f)
            else:
                source_files['file'].append(f)
        for typ in ['dir', 'file']:
            if self.config[typ]['rename']:
                for filter_config in self.config[typ]['filter']:
                    file_filter = make_filter(filter_config, self.filters)
                    source_files[typ] = file_filter.apply(source_files[typ])
            else:
                source_files[typ] = []
        return source_files
    
    def check_rules(self, source_files, target_files):
        for typ in ['dir', 'file']:
            # 1. Check rename target numbers
            ns = len(source_files[typ])
            nt = len(target_files[typ])
            if ns != nt:
                raise Exception(
                    f'Number of records not matching, source has {ns} {typ}, but target has {nt} {typ}')
            # 2. Check duplicate targets
            cnt = Counter(target_files[typ])
            for t, c in cnt.items():
                if c > 1:
                    raise Exception(
                        f'Target naming collision {c} times for: {t}')
            # 3. Check if target already exists
            for i, t in enumerate(target_files[typ]):
                if t.exists() and t.resolve() != source_files[typ][i].resolve():
                    raise Exception(f'Target already exists and not the same as source: {t}')


    def rename_recursive(self, path: Path, apply=False) -> Path:
        with chdir(path):
            # 1. Rename current dir
            # Determine and filter files
            source_files = self.filter_files(path)
            # Enable/Disable renaming for file/dir
            for typ in ['dir', 'file']:
                if not self.config[typ]['rename']:
                    source_files[typ] = []
            # Prepare target file list
            target_files = copy.deepcopy(source_files)


            # Apply rename rules
            for typ in ['dir', 'file']:
                for i, t in enumerate(target_files[typ]):
                    self.logger.debug(f'Renaming {typ} -- {t.name}')
                    for r in self.renamers:
                        nt, applied = r.apply(t, typ)
                        if applied:
                            t = nt
                            self.logger.debug(f'    --[{r.desc:40}]-->{t.name}')
                        else:
                            if t != nt:
                                raise Exception(f'Rule [{m.desc:40}] not applied but path changed from {t} to {nt}')
                    self.logger.debug(f'    --[{"Final result":40}]-->{t}')
                    target_files[typ][i] = t

            # Check rules
            self.check_rules(source_files, target_files)

            if apply:
                for typ in ['dir', 'file']:
                    for i in range(len(source_files[typ])):
                        src = source_files[typ][i]
                        tgt = target_files[typ][i]
                        if src.resolve() == tgt.resolve():
                            continue
                        self.logger.info(f'Apply renaming: {src} \n{"":91}--> {tgt}', extra={
                                         'info': {'op': 'rename', 'src': str(src), 'tgt': str(tgt)}})
                        src.rename(tgt)

            # 2. Rename sub dirs
            if apply:
                sub_dirs = target_files['dir']
            else:
                sub_dirs = source_files['dir']
            for d in sub_dirs:
                self.rename_recursive(d, apply)

    def move_files(self, source: Path, target: Path, apply=False) -> bool:
        '''Move every file/dir under source dir to target dir, non-recursively'''
        self.logger.info(f'Moving files from {source} to {target}')
        with chdir(source):
            # Determine and filter files
            source_files = self.filter_files(source)
            target_files = copy.deepcopy(source_files)

            # Apply move rules
            for typ in ['dir', 'file']:
                for i, t in enumerate(target_files[typ]):
                    self.logger.debug(f'Moving {typ} -- {t.name}')
                    t = target.resolve() / t.name
                    self.logger.debug(f'    --[{"Set target path":40}]-->{t}')
                    for m in self.movers:
                        nt, applied = m.apply(t, typ)
                        if applied:
                            t = nt
                            self.logger.debug(f'    --[{m.desc:40}]-->{t}')
                        else:
                            if t != nt:
                                raise Exception(f'Rule [{m.desc:40}] not applied but path changed from {t} to {nt}')
                    self.logger.debug(f'    --[{"Final result":40}]-->{t}')
                    target_files[typ][i] = t

            self.check_rules(source_files, target_files)

        any_file_moved = False
        if apply:
            for typ in ['dir', 'file']:
                for i in range(len(source_files[typ])):
                        src = source_files[typ][i]
                        tgt = target_files[typ][i]
                        self.logger.info(f'Moving file: {src} \n{"":88}--> {tgt}', extra={
                                         'info': {'op': 'move', 'src': str(src), 'tgt': str(tgt)}})
                        any_file_moved = True
                        with chmkdir(tgt.parent):
                            src.rename(tgt)
        return any_file_moved
        
                    