"""Separate bundled read-only resources from the installed executable."""
import sys
from pathlib import Path


def resource_path(relative_path):
    # Nuitka onefile extracts bundled data (including icon.ico) into its
    # temporary runtime directory.  __file__ points there at runtime, while
    # sys.argv[0] points to the outer EXE and therefore cannot find data files.
    if '__compiled__' in globals():
        root = Path(__file__).resolve().parent
    elif getattr(sys, 'frozen', False):
        root = Path(sys.executable).resolve().parent
    else:
        root = Path(__file__).resolve().parent
    return str(root / relative_path)


def is_compiled():
    return '__compiled__' in globals() or bool(getattr(sys, 'frozen', False))


def launcher_executable():
    if '__compiled__' in globals():
        return str(Path(sys.argv[0]).resolve())
    if getattr(sys, 'frozen', False):
        return str(Path(sys.executable).resolve())
    return str(Path(resource_path('run.py')))
