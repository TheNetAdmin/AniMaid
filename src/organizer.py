from .filter import make_filter
from pathlib import Path
import logging
import re
from .utils import chdir

class renamer:
    def __init__(self, rule):
        self.rule = rule
        self.desc = rule['description']
        self.type = rule['type']
        self.regex = rule['regex']
        self.file = rule['file']
        self.entries = []
        self.logger = logging.getLogger(f'animaid.renamer.{"_".join(self.desc.split(" "))}')
        if self.type in ['remove', 'check']:
            for e in rule['entries']:
                prefix = rule['prefix'] if 'prefix' in rule.keys() else ''
                suffix = rule['suffix'] if 'suffix' in rule.keys() else ''
                self.entries.append(prefix + e + suffix)
        else:
            self.entries = rule['entries']

    def apply(self, target: Path) -> Path:
        # Check file type
        if target.is_dir():
            if self.file not in ['dir', 'all']:
                return target
        else:
            if self.file not in ['file', 'all']:
                return target

        # Apply rules
        parent = target.parent
        name = target.name
        if self.type == 'transform':
            for e in self.entries:
                if self.regex:
                    name = re.sub(e['source'], e['target'], name)
                else:
                    name = name.replace(e['source'], e['target'])
        elif self.type == 'remove':
            for e in self.entries:
                if self.regex:
                    # self.logger.debug(f'Before applying regex rule {e}: {name}')
                    name = re.sub(e, '', name)
                    # self.logger.debug(f'After applying regex rule {e}: {name}')
                else:
                    name = name.replace(e, '')
        elif self.type == 'check':
            for e in self.entries:
                if self.regex:
                    if len(re.findall(e, name)) > 0:
                        raise Exception(f'Renaming not clean due to regex rule {e} for file {name}') 
                else:
                    if e in name:
                        raise Exception(f'Renaming not clean due to rule {e} for file {name}') 
        return parent / name

class organizer:
    def __init__(self, config):
        self.config = config
        self.filters = {}
        self.logger = logging.getLogger('animaid.organizer')
        for name, filter_config in config['filter'].items():
            self.filters[name] = make_filter(filter_config)
        self.renamers = []
        for rule in config['rule']:
            self.renamers.append(renamer(rule))
        
    def rename_single(self, target: Path) -> Path:
        for r in self.renamers:
            target = r.apply(target)
        return target
    
    def rename_recursive(self, target: Path, apply = False) -> Path:
        with chdir(target):
            # 1. Rename current dir
            # Determine and filter targets
            source_files = {'dir': [], 'file': []}
            for f in target.iterdir():
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
            
            # Apply rename rules
            target_files = source_files.copy()
            for typ in ['dir', 'file']:
                for i, t in enumerate(source_files[typ]):
                    self.logger.debug(f'Renaming {typ} -- {t.name}')
                    for r in self.renamers:
                        t = r.apply(t)
                        self.logger.debug(f'    --[{r.desc:30}]-->{t}')
                    target_files[typ][i] = t
            if apply:
                # TODO
                pass

            # 2. Rename sub dirs
            if apply:
                sub_dirs = target_files['dir']
            else:
                sub_dirs = source_files['dir']
            for d in sub_dirs:
                self.rename_recursive(d, apply)