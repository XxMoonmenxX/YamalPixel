import requests
import json
import os
import sys
from urllib.parse import urljoin


def get_neoforge_versions():
    """Получить список доступных версий NeoForge"""
    base_url = "https://maven.neoforged.net/releases/net/neoforged/neoforge/"

    try:
        response = requests.get(base_url + "maven-metadata.xml")
        response.raise_for_status()

        # Парсим XML для получения версий
        from xml.etree import ElementTree as ET
        root = ET.fromstring(response.content)

        versions = []
        for version_elem in root.findall(".//version"):
            versions.append(version_elem.text)

        return sorted(versions, reverse=True)

    except Exception as e:
        print(f"Ошибка при получении списка версий: {e}")
        return []


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

    versions = get_neoforge_versions()

    if not versions:
        print("Не удалось получить список версий.")
        print("Пожалуйста, введите версию вручную.")
        version = input("Введите версию NeoForge (например: 20.4.100): ").strip()
    else:
        print("\nДоступные версии (последние 10):")
        for i, ver in enumerate(versions[:10], 1):
            print(f"{i}. {ver}")

        print("\n0. Ввести версию вручную")

        try:
            choice = input("\nВыберите версию (номер) или введите свою: ").strip()

            if choice == "0":
                version = input("Введите версию NeoForge: ").strip()
            elif choice.isdigit() and 1 <= int(choice) <= len(versions[:10]):
                version = versions[int(choice) - 1]
            else:
                # Если пользователь ввел версию напрямую
                version = choice
        except (ValueError, IndexError):
            version = input("Введите версию NeoForge: ").strip()

    if not version:
        print("Версия не указана. Выход.")
        return

    print(f"\nСкачивание NeoForge версии: {version}")

    if download_neoforge(version):
        print(f"\nNeoForge {version} успешно скачан!")
        print(f"Запустите: java -jar neoforge-{version}-installer.jar")
    else:
        print(f"\nНе удалось скачать NeoForge {version}")
        print("Проверьте правильность версии и подключение к интернету.")


if __name__ == "__main__":
    main()