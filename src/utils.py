import contextlib
import os
import shutil
from pathlib import Path


@contextlib.contextmanager
def chmkdir(path):
    """Go to working directory and return to previous on exit."""
    prev_cwd = Path.cwd()
    Path(path).mkdir(parents=True, exist_ok=True)
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


@contextlib.contextmanager
def chdir(path):
    """Go to working directory and return to previous on exit."""
    prev_cwd = Path.cwd()
    Path(path)
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def check_and_copy(source, target):
    if not target.exists():
        shutil.copy(source, target)
