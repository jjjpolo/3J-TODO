import os
import sys


def get_app_base_dir() -> str:
    """Return the writable app directory.

    - In PyInstaller EXE mode: folder where the EXE is located.
    - In source mode: project root folder.
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def get_runtime_file(filename: str) -> str:
    return os.path.join(get_app_base_dir(), filename)


def get_bundled_file(filename: str) -> str:
    """Return file path from bundled resources when available."""
    bundle_dir = getattr(sys, '_MEIPASS', get_app_base_dir())
    return os.path.join(bundle_dir, filename)
