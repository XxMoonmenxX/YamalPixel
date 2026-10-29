"""Build and check the launcher without deleting previous builds or user data."""
import argparse
import ast
import ctypes
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
MODULES = ('PyQt6', 'requests', 'aiohttp', 'bs4', 'pygame', 'pypresence', 'mcstatus', 'psutil')


def project_version(root):
    for node in ast.parse((root / 'ConfDir' / 'Versions.py').read_text(encoding='utf-8')).body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == 'CURRENT_VERSION' for target in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError('CURRENT_VERSION не найден')


def output_executable(output_dir, standalone=False):
    name = 'YamalPixelLauncher.exe' if os.name == 'nt' else 'YamalPixelLauncher'
    return Path(output_dir) / ('run.dist' if standalone else '') / name


def check_output_available(path):
    """Check Windows delete sharing before spending time on compilation."""
    if os.name != 'nt' or not path.exists():
        return
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                  wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateFileW(str(path), 0x40010000, 0, None, 3, 0x80, None)
    if handle == ctypes.c_void_p(-1).value:
        error = ctypes.get_last_error()
        raise PermissionError(error, f'Не удаётся заменить {path}. Закройте запущенный лаунчер '
                              'и проверьте права на файл или выберите --output-dir другую_папку.')
    kernel.CloseHandle(handle)


def build_command(root=ROOT, standalone=False, console=False, output_dir=None, jobs=4, lto=False):
    root = Path(root).resolve()
    output_dir = Path(output_dir or root / 'dist' / 'nuitka').resolve()
    version = project_version(root)
    numeric = '.'.join((version.split('.') + ['0'] * 4)[:4])
    command = [sys.executable, '-m', 'nuitka', '--standalone' if standalone else '--onefile',
               '--enable-plugin=pyqt6', '--assume-yes-for-downloads',
               f'--jobs={jobs}', '--lto=yes' if lto else '--lto=no',
               '--output-dir=' + str(output_dir),
               '--output-filename=' + output_executable(output_dir).name,
               '--report=' + str(output_dir / 'compilation-report.xml')]
    for package in ('ConfDir', 'Core', 'Ui', 'Network', 'MCLIB'):
        command.append('--include-package=' + package)
    command += ['--include-package-data=MCLIB:version.txt',
                '--include-package-data=certifi',
                '--include-distribution-metadata=pygame-ce',
                '--nofollow-import-to=tkinter', '--nofollow-import-to=PyQt5',
                '--nofollow-import-to=PySide6', '--nofollow-import-to=pytest',
                '--nofollow-import-to=pygame.tests', '--nofollow-import-to=aiohttp.test_utils']
    for directory in ('Ui/assets', 'YamalPixelRes'):
        if (root / directory).is_dir():
            command.append(f'--include-data-dir={root / directory}={directory}')
    for filename in ('icon.ico', 'Comfortaa-VariableFont_wght.ttf'):
        if (root / filename).is_file():
            command.append(f'--include-data-files={root / filename}={filename}')
    # Embed local launcher settings in the onefile build.  The file is ignored
    # by Git and can be overridden by a .env placed next to the EXE.
    if (root / '.env').is_file():
        command.append(f'--include-data-files={root / ".env"}=.env')
    if os.name == 'nt':
        command += ['--windows-console-mode=force' if console else '--windows-console-mode=disable',
                    '--file-version=' + numeric, '--product-version=' + numeric,
                    '--file-description=YamalPixel Launcher', '--product-name=YamalPixel Launcher',
                    '--company-name=YamalPixel']
        if (root / 'icon.ico').is_file():
            command.append('--windows-icon-from-ico=' + str(root / 'icon.ico'))
    command.append(str(root / 'run.py'))
    return command


def smoke_test(executable, output_dir):
    report = Path(output_dir) / 'smoke-test.json'
    if report.exists():
        report.unlink()
    with tempfile.TemporaryDirectory(prefix='yamalpixel-build-check-') as directory:
        environment = dict(os.environ, USERPROFILE=directory, HOME=directory,
                           QT_QPA_PLATFORM='offscreen', SDL_AUDIODRIVER='dummy', PYTHONUTF8='1')
        result = subprocess.run([str(executable), '--smoke-test', '--smoke-report', str(report)],
                                cwd=directory, env=environment, timeout=90,
                                capture_output=True, text=True, encoding='utf-8', errors='replace')
        if report.exists():
            details = json.loads(report.read_text(encoding='utf-8'))
            if result.returncode == 0 and details.get('ok'):
                print('Проверка EXE пройдена: ' + ', '.join(details['checks']))
                return True
            print(json.dumps(details, ensure_ascii=False, indent=2))
        print('Проверка EXE не пройдена. Код: ' + str(result.returncode))
        print(result.stdout[-3000:] + result.stderr[-3000:])
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(description='Сборка YamalPixel Launcher через Nuitka')
    parser.add_argument('--standalone', action='store_true', help='EXE с зависимостями в папке вместо одного EXE')
    parser.add_argument('--console', action='store_true', help='Показать консоль для диагностики')
    parser.add_argument('--install-deps', action='store_true', help='Установить requirements-build.txt этим Python')
    parser.add_argument('--dry-run', action='store_true', help='Только показать команду')
    parser.add_argument('--skip-smoke-test', action='store_true', help='Пропустить проверку собранного EXE')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist' / 'nuitka')
    parser.add_argument('--jobs', type=int, default=min(os.cpu_count() or 2, 8))
    parser.add_argument('--lto', action='store_true', help='Включить более долгую оптимизацию при линковке')
    args = parser.parse_args(argv)
    if args.jobs < 1:
        parser.error('--jobs должен быть положительным')
    if sys.version_info < (3, 12):
        parser.error('Нужен Python 3.12 или новее')
    args.output_dir = args.output_dir.resolve()
    command = build_command(ROOT, args.standalone, args.console, args.output_dir, args.jobs, args.lto)
    if args.dry_run:
        print(subprocess.list2cmdline(command))
        return 0
    try:
        check_output_available(output_executable(args.output_dir, args.standalone))
        if args.install_deps:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(ROOT / 'requirements-build.txt')],
                           cwd=ROOT, check=True)
        missing = [name for name in ('nuitka', 'ordered_set', 'zstandard', *MODULES)
                   if importlib.util.find_spec(name) is None]
        if missing:
            print('Не установлены: ' + ', '.join(missing))
            print('Запустите build.py --install-deps этим же Python.')
            return 1
        for filename in ('run.py', 'icon.ico', 'MCLIB/version.txt', 'Ui/assets/chevron-down.svg'):
            if not (ROOT / filename).is_file():
                raise FileNotFoundError('Отсутствует ресурс: ' + filename)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        print('Python: ' + sys.executable, flush=True)
        result = subprocess.run(command, cwd=ROOT)
        if result.returncode:
            return result.returncode
        executable = output_executable(args.output_dir, args.standalone)
        if not executable.is_file():
            raise FileNotFoundError('Nuitka не создала ' + str(executable))
        if not args.skip_smoke_test and not smoke_test(executable, args.output_dir):
            return 1
        print('Готово: ' + str(executable))
        if args.standalone:
            print('Для переноса нужна вся папка ' + str(executable.parent))
        return 0
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        print('Ошибка сборки: ' + str(exc))
        return 1


if __name__ == '__main__':
    sys.exit(main())
