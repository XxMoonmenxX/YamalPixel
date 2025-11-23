# utils/system_utils.py
import os
import platform
import psutil
import shutil
import subprocess

def get_system_info():
    """Собирает информацию о системе."""
    info = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": psutil.cpu_count(logical=True),
        "memory_total": psutil.virtual_memory().total,
        "memory_available": psutil.virtual_memory().available,
        "disk_total": shutil.disk_usage("/").total,
        "disk_free": shutil.disk_usage("/").free,
    }
    return info

def is_admin():
    """Проверяет, запущен ли скрипт от имени администратора."""
    try:
        return os.getuid() == 0 # Linux/MacOS
    except AttributeError:
        import ctypes
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() # Windows
        except:
            return False # В случае ошибки предполагаем, что нет прав

def check_ram(required_gb=3):
    """Проверяет, достаточно ли оперативной памяти (в ГБ)."""
    required_bytes = required_gb * 1024 * 1024 * 1024
    available = psutil.virtual_memory().available
    return available >= required_bytes

def check_disk_space(path, required_gb=2):
    """Проверяет, достаточно ли места на диске (в ГБ) для указанного пути."""
    required_bytes = required_gb * 1024 * 1024 * 1024
    free_space = shutil.disk_usage(path).free
    return free_space >= required_bytes

def is_minecraft_running():
    """Проверяет, запущен ли процесс Minecraft."""
    for proc in psutil.process_iter(['name']):
        try:
            if 'minecraft' in proc.info['name'].lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False

def get_process_by_name(name):
    """Возвращает список процессов с указанным именем."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if name.lower() in proc.info['name'].lower():
                processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return processes

def kill_process_by_name(name):
    """Убивает все процессы с указанным именем."""
    processes = get_process_by_name(name)
    killed_count = 0
    for proc in processes:
        try:
            proc.kill()
            proc.wait() # Ждем завершения
            killed_count += 1
            print(f"Убит процесс: {proc.name()} (PID: {proc.pid})")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(f"Ошибка убийства процесса {proc.name()} (PID: {proc.pid}): {e}")
    return killed_count
