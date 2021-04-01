import contextlib
from pathlib import Path
import os
import shutil

@contextlib.contextmanager
def working_directory(path):
    """Go to working directory and return to previous on exit."""
    prev_cwd = Path.cwd()
    Path(path).mkdir(parents=True, exist_ok=True)
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)

def check_and_copy(source, target):
    if not target.exists():
        shutil.copy(source, target)