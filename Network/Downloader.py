# downloader.py
import os
import time
import hashlib
import requests
import aiohttp
import asyncio
import logging
import zipfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
from tkinter import ttk, messagebox
import threading

class LauncherCache:
    def __init__(self):
        self.cache_dir = Path.home() / ".yamalpixel_cache"
        self.cache_dir.mkdir(exist_ok=True)

    def is_cache_fresh(self, cache_file, max_age_hours=24):
        """Проверяет свежесть кэша"""
        if not cache_file.exists():
            return False

        file_age = time.time() - cache_file.stat().st_mtime
        return file_age < (max_age_hours * 3600)

    def get_file_hash(self, url):
        """Создает хеш для имени файла кэша"""
        return hashlib.md5(url.encode()).hexdigest()

    def download_and_cache(self, url, cache_file):
        """Скачивает и кэширует файл"""
        try:
            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            with open(cache_file, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192 * 4):
                    f.write(chunk)

            logging.info(f"Файл закэширован: {cache_file.name}")
        except Exception as e:
            logging.error(f"Ошибка кэширования {url}: {e}")
            raise

    def get_cached_file(self, url, force_refresh=False):
        """Возвращает кэшированный файл или качает новый"""
        file_hash = self.get_file_hash(url)
        cache_file = self.cache_dir / file_hash

        if cache_file.exists() and not force_refresh:
            if self.is_cache_fresh(cache_file):
                return cache_file

        # Качаем и кэшируем
        self.download_and_cache(url, cache_file)
        return cache_file


class TurboDownloader:
    def __init__(self):
        self.cache = {}
        self.cache_manager = LauncherCache()
        self._session = None

    @property
    def session(self):
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=300)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def cleanup(self):
        """Закрывает сессию при завершении"""
        if self._session:
            await self._session.close()
            self._session = None

    async def get_turbo_link(self, public_key):
        """Быстрое получение ссылки через асинхронность"""
        if public_key in self.cache:
            return self.cache[public_key]

        api_url = "https://cloud-api.yandex.net/v1/disk/public/resources/download"
        try:
            async with self.session.get(
                api_url, params={"public_key": public_key}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    direct_link = data.get("href")
                    self.cache[public_key] = direct_link
                    return direct_link
                else:
                    logging.error(f"Ошибка API Яндекс: {response.status}")
                    return None
        except asyncio.TimeoutError:
            logging.error("Таймаут получения ссылки Яндекс")
            return None
        except Exception as e:
            logging.error(f"Ошибка получения ссылки: {e}")
            return None

    async def download_file_async(self, url, file_path, progress_callback=None):
        """Турбо-загрузка с прогрессом"""
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")

                total_size = int(response.headers.get("content-length", 0))

                with open(file_path, "wb") as f:
                    downloaded = 0
                    async for chunk in response.content.iter_chunked(8192 * 8):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded, total_size)

                return True
        except Exception as e:
            logging.error(f"Ошибка загрузки {url}: {e}")
            return False

    def download_file_sync(self, url, file_path, progress_callback=None):
        """Синхронная версия для использования в потоках"""
        try:
            return asyncio.run(
                self.download_file_async(url, file_path, progress_callback)
            )
        finally:
            asyncio.run(self.cleanup())


def download_single_mod_turbo(mod_info, minecraft_dir):
    """Турбо-загрузка одного мода с правильным закрытием ресурсов"""
    downloader = TurboDownloader()
    try:
        print(f"🔍 Начинаем загрузку мода: {mod_info['file']}")

        # Получаем прямую ссылку
        direct_link = asyncio.run(downloader.get_turbo_link(mod_info["url"]))
        print(f"🔗 Прямая ссылка получена: {direct_link is not None}")

        if not direct_link:
            logging.error(f"Не удалось получить ссылку для {mod_info['file']}")
            asyncio.run(downloader.cleanup())
            return False

        # Путь для сохранения
        mods_dir = os.path.join(minecraft_dir, "mods")
        os.makedirs(mods_dir, exist_ok=True)
        file_path = os.path.join(mods_dir, mod_info["file"])

        # Загружаем файл
        success = downloader.download_file_sync(direct_link, file_path)
        print(
            f"📥 Результат загрузки {mod_info['file']}: {'✅ Успех' if success else '❌ Ошибка'}"
        )

        if success and mod_info["file"].endswith(".zip"):
            # Распаковываем ZIP
            try:
                with zipfile.ZipFile(file_path, "r") as zip_ref:
                    zip_ref.extractall(mods_dir)
                print(f"📦 Мод распакован: {mod_info['file']}")
            except Exception as e:
                logging.error(f"Ошибка распаковки {mod_info['file']}: {e}")

        # Явно закрываем загрузчик
        asyncio.run(downloader.cleanup())
        return success

    except Exception as e:
        logging.error(f"Ошибка загрузки мода {mod_info['file']}: {e}")
        try:
            asyncio.run(downloader.cleanup())
        except:
            pass
        return False


def download_mods_turbo_ui(mods_list, minecraft_dir, win):
    """Версия с UI для использования в лаунчере"""

    # Создаем окно прогресса
    progress_window = tk.Toplevel(win)
    progress_window.title("Загрузка модов")
    progress_window.geometry("400x150")

    progress_label = ttk.Label(progress_window, text="Подготовка к загрузке...")
    progress_label.pack(pady=10)

    progress = ttk.Progressbar(
        progress_window, orient="horizontal", length=300, mode="determinate"
    )
    progress.pack(pady=10)

    status_label = ttk.Label(progress_window, text=f"0/{len(mods_list)} модов")
    status_label.pack()

    def download_thread():
        total_mods = len(mods_list)
        success_count = 0

        def update_progress(current, total, mod_name=""):
            percent = (current * 100) // total
            progress["value"] = percent
            status_label.config(text=f"{current}/{total} модов - {mod_name}")
            progress_window.update()

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = []

            for i, mod in enumerate(mods_list):
                future = executor.submit(download_single_mod_turbo, mod, minecraft_dir)
                futures.append((future, mod["file"]))

            # Обновляем прогресс
            for i, (future, mod_name) in enumerate(futures):
                try:
                    win.after(0, lambda: update_progress(i, total_mods, mod_name))
                    success = future.result(timeout=180)
                    if success:
                        success_count += 1

                    win.after(0, lambda: update_progress(i + 1, total_mods, mod_name))

                except Exception as e:
                    logging.error(f"Ошибка в потоке загрузки {mod_name}: {e}")

        # Финальное сообщение
        win.after(0, lambda: show_download_result(success_count, total_mods, progress_window))

    def show_download_result(success, total, window):
        window.destroy()
        if success == total:
            messagebox.showinfo(
                "Загрузка завершена", f"✅ Все {success} модов успешно загружены!"
            )
        else:
            messagebox.showwarning(
                "Загрузка завершена",
                f"📊 Загружено {success} из {total} модов\n\n"
                f"Некоторые моды могли не загрузиться. Проверьте логи.",
            )

    threading.Thread(target=download_thread, daemon=True).start()

