import requests
import json
import os
import sys
from urllib.parse import urljoin
from YamalPixel_Launcher import is_neoforge_needed

def download_neoforge(version):
    """Скачать указанную версию NeoForge"""
    base_url = f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{version}/"

    # Формируем имя файла
    filename = f"neoforge-{version}-installer.jar"
    download_url = base_url + filename

    print(f"Попытка скачивания: {download_url}")

    try:
        # Проверяем доступность файла
        response = requests.head(download_url)
        if response.status_code != 200:
            print(f"Файл не найден. Пробуем альтернативное имя...")
            # Пробуем альтернативный формат имени
            filename = f"neoforge-{version}.jar"
            download_url = base_url + filename
            response = requests.head(download_url)
            if response.status_code != 200:
                print(f"Ошибка: Не удалось найти файл для версии {version}")
                return False

        # Скачиваем файл
        print(f"Скачивание NeoForge {version}...")
        response = requests.get(download_url, stream=True)
        response.raise_for_status()

        # Сохраняем файл
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        file_size = os.path.getsize(filename) / (1024 * 1024)  # Размер в МБ
        print(f"Успешно скачано: {filename} ({file_size:.2f} MB)")
        return True

    except Exception as e:
        print(f"Ошибка при скачивании: {e}")
        return False


def main():
    print("=== NeoForge Downloader ===")
    print("Получение списка доступных версий...")

    version = is_neoforge_needed(selected_version)


    if download_neoforge(version):
        print(f"\nNeoForge {version} успешно скачан!")
        print(f"Запустите: java -jar neoforge-{version}-installer.jar")
    else:
        print(f"\nНе удалось скачать NeoForge {version}")
        print("Проверьте правильность версии и подключение к интернету.")


if __name__ == "__main__":
    main()