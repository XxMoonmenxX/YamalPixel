import requests
import os
import json
import urllib.parse
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from ttkthemes import ThemedTk
from pathlib import Path
import sys
import threading
import re
from datetime import datetime
import shutil
import subprocess

win = ThemedTk(theme="arc")

CONFIG = {
    "version": "1.20.1",
    "fabric_loader": "0.17.2",
    "minecraft_dir": os.path.expanduser("~/YamalPixel")}


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # В режиме разработки используем домашнюю директорию
        base_path = Path.home() / "YamalPixelRes"

    return os.path.join(base_path, relative_path)


def set_window_icon(window):
    """Set icon for all windows"""
    try:
        icon_path = resource_path("icon.ico")

        # Дополнительная проверка для PyInstaller
        if not os.path.exists(icon_path):
            # Пробуем найти в домашней директории
            home_icon_path = Path.home() / "YamalPixelRes" / "icon.ico"
            if os.path.exists(home_icon_path):
                icon_path = home_icon_path
            else:
                print(f"Icon not found: {icon_path}")
                return

        window.iconbitmap(icon_path)
        print(f"Icon loaded from: {icon_path}")

    except Exception as e:
        print(f"Icon error: {e}")


class ModrinthAPI:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://api.modrinth.com/v2"
        self.session.headers.update(
            {"User-Agent": "YamalPixel-Launcher/1.0 (moonmen@example.com)"}
        )

        # Поддерживаемые версии и загрузчики
        self.supported_versions = {
            "fabric": [
                "1.14.4", "1.15.2", "1.16.5", "1.17.1", "1.18.2",
                "1.19.2", "1.19.4", "1.20.1", "1.20.2", "1.20.3", "1.20.4",
                "1.20.6", "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"
            ],
            "neoforge": [
                "1.20.1", "1.20.2", "1.20.3", "1.20.4", "1.20.6",
                "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"
            ],
            "forge": [
                "1.14.4", "1.15.2", "1.16.5", "1.17.1", "1.18.2",
                "1.19.2", "1.19.4", "1.20.1", "1.20.2", "1.20.3", "1.20.4",
                "1.20.6", "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"
            ],
            "quilt": [
                "1.18.2", "1.19.2", "1.19.4", "1.20.1", "1.20.2", "1.20.3", "1.20.4",
                "1.20.6", "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"
            ]
        }

    def get_supported_loaders(self, minecraft_version):
        """Получить доступные загрузчики для версии Minecraft"""
        available_loaders = []
        for loader, versions in self.supported_versions.items():
            if minecraft_version in versions:
                available_loaders.append(loader)
        return available_loaders

    def search_mods(self, query, limit=30):
        """Поиск модов на Modrinth"""
        try:
            url = f"{self.base_url}/search"
            params = {"query": query, "limit": limit, "index": "relevance"}
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Ошибка поиска модов: {e}")
            return None

    def get_mod_versions(self, mod_id, minecraft_version, loader):
        try:
            url = f"{self.base_url}/project/{mod_id}/version"
            # Передаём как JSON-строки
            params = {
                "game_versions": f'["{minecraft_version}"]',
                "loaders": f'["{loader}"]',
            }
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            versions = response.json()

            # Фильтруем версии, у которых есть JAR-файл
            return [
                v for v in versions
                if v.get("files") and any(f["filename"].endswith(".jar") for f in v["files"])
            ]

        except Exception as e:
            print(f"Ошибка получения версий мода {mod_id}: {e}")
            return None

    import urllib.parse

    def download_mod(self, project_slug, version_id, filename, mods_dir):
        """Скачивание мода с правильным экранированием имени файла"""
        try:
            # Экранируем имя файла — особенно важно для +, пробелов, % и т.д.
            encoded_filename = urllib.parse.quote(filename)

            # Правильный URL
            file_url = f"https://cdn.modrinth.com/data/{project_slug}/versions/{version_id}/{encoded_filename}"

            print(f"📥 Скачиваем: {file_url}")

            response = self.session.get(file_url, stream=True, timeout=30)
            response.raise_for_status()

            filepath = os.path.join(mods_dir, filename)
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            print(f"✅ Успешно скачан: {filename}")
            return True

        except Exception as e:
            print(f"❌ Ошибка скачивания мода {filename}: {e}")
            return self.download_mod_alternative(project_slug, version_id, filename, mods_dir)

    def download_mod_alternative(self, _project_slug, version_id, filename, mods_dir):
        """Альтернативный метод скачивания через получение информации о версии"""
        try:
            # Получаем информацию о версии
            version_url = f"{self.base_url}/version/{version_id}"
            response = self.session.get(version_url, timeout=30)
            response.raise_for_status()
            version_data = response.json()

            print(f"🔍 Ищем файл в информации о версии: {filename}")

            if "files" in version_data and version_data["files"]:
                # Ищем нужный файл по имени
                target_file = None
                for file_info in version_data["files"]:
                    if file_info["filename"] == filename:
                        target_file = file_info
                        break

                if target_file and "url" in target_file:
                    download_url = target_file["url"]
                    print(f"📥 Альтернативное скачивание: {download_url}")

                    response = self.session.get(download_url, stream=True, timeout=30)
                    response.raise_for_status()

                    filepath = os.path.join(mods_dir, filename)
                    with open(filepath, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    print(f"✅ Успешно скачан альтернативным методом: {filename}")
                    return True

            print(f"❌ Файл {filename} не найден в информации о версии")
            return False

        except Exception as e:
            print(f"❌ Альтернативный метод скачивания также не удался: {e}")
            return False


# Функция создания новой сборки с выбором модов
# === Глобальные переменные для сортировки ===
current_sort_col = "downloads"
current_sort_reverse = False


def create_new_collection():
    """Создаёт окно для создания новой сборки модов"""
    global current_sort_col, current_sort_reverse
    collection_window = tk.Toplevel(win)
    collection_window.title("Создать сборку")
    collection_window.geometry("900x1080")
    collection_window.transient(win)
    collection_window.grab_set()

    main_frame = ttk.Frame(collection_window, padding=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(
        main_frame, text="📦 Новая сборка модов", font=("Comfortaa", 16, "bold")
    ).pack(pady=(0, 20))

    # === Основные настройки ===
    settings_frame = ttk.Frame(main_frame)
    settings_frame.pack(fill="x", pady=(0, 20))

    ttk.Label(settings_frame, text="Название:").pack(anchor="w")
    name_var = tk.StringVar()
    ttk.Entry(settings_frame, textvariable=name_var, width=50).pack(
        fill="x", pady=(0, 10)
    )

    meta_frame = ttk.Frame(settings_frame)
    meta_frame.pack(fill="x")

    ttk.Label(meta_frame, text="Версия:").pack(side="left")
    version_var = tk.StringVar(value="1.20.1")

    all_versions = [
        "1.14.4", "1.15.2", "1.16.5", "1.17.1", "1.18.2",
        "1.19.2", "1.19.4", "1.20.1", "1.20.2", "1.20.3", "1.20.4",
        "1.20.6", "1.21", "1.21.1", "1.21.2", "1.21.3", "1.21.4"
    ]

    version_combo = ttk.Combobox(
        meta_frame,
        textvariable=version_var,
        values=all_versions,
        state="readonly",
        width=12,
    )
    version_combo.pack(side="left", padx=(5, 20))

    ttk.Label(meta_frame, text="Загрузчик:").pack(side="left")
    loader_var = tk.StringVar(value="fabric")

    api = ModrinthAPI()

    def update_loaders(*args):
        """Обновляет список загрузчиков при смене версии"""
        selected_version = version_var.get()
        available_loaders = api.get_supported_loaders(selected_version)

        loader_combo['values'] = available_loaders
        if loader_var.get() not in available_loaders and available_loaders:
            loader_var.set(available_loaders[0])

    version_var.trace_add('write', update_loaders)

    loader_combo = ttk.Combobox(
        meta_frame,
        textvariable=loader_var,
        values=api.get_supported_loaders(version_var.get()),
        state="readonly",
        width=12,
    )
    loader_combo.pack(side="left", padx=5)

    update_loaders()

    # === Вкладки модов ===
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill="both", expand=True, pady=(0, 20))

    # --- Локальные моды ---
    local_frame = ttk.Frame(notebook, padding=10)
    notebook.add(local_frame, text="📁 Мои моды")

    local_search_frame = ttk.Frame(local_frame)
    local_search_frame.pack(fill="x", pady=(0, 10))

    ttk.Label(local_search_frame, text="Поиск:").pack(side="left")
    local_search_var = tk.StringVar()
    local_search_entry = ttk.Entry(
        local_search_frame, textvariable=local_search_var, width=30
    )
    local_search_entry.pack(side="left", padx=(5, 10))

    def search_local_mods():
        query = local_search_var.get().lower()
        load_local_mods(query)

    ttk.Button(local_search_frame, text="🔍 Поиск", command=search_local_mods).pack(
        side="left", padx=(0, 10)
    )
    ttk.Button(
        local_search_frame, text="🔄 Обновить", command=lambda: load_local_mods()
    ).pack(side="left")

    local_tree_frame = ttk.Frame(local_frame)
    local_tree_frame.pack(fill="both", expand=True)

    local_mods_tree = ttk.Treeview(
        local_tree_frame, columns=("name", "file", "size"), show="headings", height=10
    )
    local_mods_tree.heading("name", text="Название")
    local_mods_tree.heading("file", text="Файл")
    local_mods_tree.heading("size", text="Размер")

    local_mods_tree.column("name", width=250)
    local_mods_tree.column("file", width=200)
    local_mods_tree.column("size", width=80)

    def load_local_mods(search_query=None):
        local_mods_tree.delete(*local_mods_tree.get_children())
        mods_dir = os.path.join(CONFIG["minecraft_dir"], "mods")

        if not os.path.exists(mods_dir):
            return

        for file in os.listdir(mods_dir):
            if file.endswith(".jar"):
                if search_query and search_query not in file.lower():
                    continue

                file_path = os.path.join(mods_dir, file)
                try:
                    size = os.path.getsize(file_path) / 1024 / 1024
                    name = " ".join(
                        [
                            word.capitalize()
                            for word in file.replace(".jar", "")
                            .replace("_", " ")
                            .replace("-", " ")
                            .split()
                        ]
                    )
                    local_mods_tree.insert(
                        "", "end", values=(name, file, f"{size:.1f} MB"), tags=(file,)
                    )
                except (OSError, FileNotFoundError) as e:
                    print(f"⚠️ Не удалось прочитать файл {file}: {e}")

    local_scrollbar = ttk.Scrollbar(
        local_tree_frame, orient="vertical", command=local_mods_tree.yview
    )
    local_mods_tree.configure(yscrollcommand=local_scrollbar.set)

    local_mods_tree.pack(side="left", fill="both", expand=True)
    local_scrollbar.pack(side="right", fill="y")

    load_local_mods()

    # --- Modrinth ---
    modrinth_frame = ttk.Frame(notebook, padding=10)
    notebook.add(modrinth_frame, text="🌐 Modrinth")

    search_frame = ttk.Frame(modrinth_frame)
    search_frame.pack(fill="x", pady=(0, 10))

    ttk.Label(search_frame, text="Поиск модов:").pack(side="left")
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var, width=30)
    search_entry.pack(side="left", padx=(5, 10))

    def search_modrinth():
        """Поиск модов: сначала ищем, потом помечаем совместимость"""
        query = search_var.get().strip()
        if not query:
            messagebox.showwarning("Поиск", "Введите название мода")
            return

        # Текущие настройки
        minecraft_version = version_var.get()
        loader_type = loader_var.get().lower()

        progress_window = tk.Toplevel(collection_window)
        set_window_icon(progress_window)
        progress_window.title("Поиск")
        progress_window.geometry("300x100")
        progress_window.transient(collection_window)
        progress_window.grab_set()

        ttk.Label(progress_window, text="🔍 Ищем моды...").pack(pady=10)
        progress = ttk.Progressbar(progress_window, mode="indeterminate")
        progress.pack(pady=10)
        progress.start()

        def do_search():
            try:
                # 1. Ищем до 30 модов
                results = api.search_mods(query, limit=30)
                collection_window.after(0, progress_window.destroy)

                if not results or "hits" not in results:
                    collection_window.after(0, lambda: messagebox.showinfo("Результат", "Ничего не найдено"))
                    return

                mods = results["hits"]

                # 2. Прогресс-бар: анализ совместимости
                compatibility_window = tk.Toplevel(collection_window)
                set_window_icon(compatibility_window)
                compatibility_window.title("Анализ совместимости")
                compatibility_window.geometry("400x120")
                compatibility_window.transient(collection_window)
                compatibility_window.grab_set()

                ttk.Label(compatibility_window, text="🔍 Анализ совместимости...").pack(pady=10)
                compat_progress = ttk.Progressbar(
                    compatibility_window, orient="horizontal", mode="determinate", length=300
                )
                compat_progress.pack(pady=5)
                compat_progress.config(maximum=len(mods))

                compat_status = tk.StringVar(value="Анализ 1 из ...")
                ttk.Label(compatibility_window, textvariable=compat_status).pack(pady=5)

                # 3. Помечаем каждый мод: совместим или нет
                for idx, mod in enumerate(mods):
                    collection_window.after(0, lambda i=idx + 1, t=len(mods): compat_status.set(f"Анализ {i} из {t}"))
                    collection_window.after(0, lambda i=idx: compat_progress.config(value=i))

                    # Проверяем совместимость
                    versions = api.get_mod_versions(
                        mod_id=mod["project_id"],
                        minecraft_version=minecraft_version,
                        loader=loader_type
                    )

                    if versions:
                        mod["compatible"] = True
                        mod["compatible_version"] = versions[0]["version_number"]
                        mod["filename"] = versions[0]["files"][0]["filename"]
                    else:
                        mod["compatible"] = False
                        mod["compatible_version"] = "❌ Нет версии"
                        mod["filename"] = "N/A"

                collection_window.after(0, compatibility_window.destroy)

                # 4. Сортируем: совместимые — вверх
                mods.sort(key=lambda m: (not m["compatible"], -m.get("downloads", 0)))

                collection_window.after(0, lambda: display_modrinth_results(mods))

            except Exception as e:
                collection_window.after(0, progress_window.destroy)
                collection_window.after(0, lambda: messagebox.showerror("Ошибка", f"Поиск не удался: {e}"))

        threading.Thread(target=do_search, daemon=True).start()

    def display_modrinth_results(mods):
        """Отображает моды с корректными tags"""
        modrinth_tree.delete(*modrinth_tree.get_children())

        for mod in mods:
            downloads = f"{mod.get('downloads', 0):,}"
            version = mod.get("compatible_version", "❌")
            status = "✅" if mod.get("compatible") else "❌"
            description = mod.get("description", "")[:80] + "..." if len(mod.get("description", "")) > 80 else mod.get(
                "description", "")

            # Вставляем строку
            item_id = modrinth_tree.insert(
                "",
                "end",
                values=(f"{mod['title']} ({version})", mod["author"], downloads, description, status),
                tags=(mod["project_id"], mod["filename"])  # ✅ Только ID и имя файла
            )

            # Назначаем цвет отдельно
            if mod.get("compatible"):
                modrinth_tree.item(item_id, tags=(mod["project_id"], mod["filename"], "compatible"))
            else:
                modrinth_tree.item(item_id, tags=(mod["project_id"], mod["filename"], "incompatible"))

        # Конфигурируем цвета
        modrinth_tree.tag_configure("compatible", background="#0a3020", foreground="white")
        modrinth_tree.tag_configure("incompatible", background="#3a1010", foreground="#ffaaaa")

    def on_treeview_sort(col):
        global current_sort_col, current_sort_reverse
        items = [(modrinth_tree.set(item, col), item) for item in modrinth_tree.get_children("")]
        if col == "downloads":
            items = [(int(item[0].replace(",", "")), item[1]) for item in items]
        else:
            items = [(item[0].lower(), item[1]) for item in items]

        items.sort(reverse=current_sort_reverse)
        for index, (_, item) in enumerate(items):
            modrinth_tree.move(item, "", index)

        current_sort_reverse = not current_sort_reverse
        update_sort_indicators(col)

    def update_sort_indicators(sorted_col):
        for col in modrinth_tree["columns"]:
            clean_text = modrinth_tree.heading(col)["text"].replace(" ▲", "").replace(" ▼", "")
            if col == sorted_col:
                indicator = " ▼" if current_sort_reverse else " ▲"
                modrinth_tree.heading(col, text=clean_text + indicator)
            else:
                modrinth_tree.heading(col, text=clean_text)

    ttk.Button(search_frame, text="🔍 Поиск", command=search_modrinth).pack(
        side="left", padx=(0, 10)
    )

    modrinth_tree_frame = ttk.Frame(modrinth_frame)
    modrinth_tree_frame.pack(fill="both", expand=True)

    modrinth_tree = ttk.Treeview(
        modrinth_tree_frame,
        columns=("name", "author", "downloads", "description", "status"),
        show="headings",
        height=15,
    )

    modrinth_tree.heading("name", text="Название", command=lambda: on_treeview_sort("name"))
    modrinth_tree.heading("author", text="Автор", command=lambda: on_treeview_sort("author"))
    modrinth_tree.heading("downloads", text="Загрузки", command=lambda: on_treeview_sort("downloads"))
    modrinth_tree.heading("description", text="Описание", command=lambda: on_treeview_sort("description"))
    modrinth_tree.heading("status", text="Совместимость")

    modrinth_tree.column("name", width=220)
    modrinth_tree.column("author", width=120)
    modrinth_tree.column("downloads", width=100)
    modrinth_tree.column("description", width=200)
    modrinth_tree.column("status", width=80)

    modrinth_scrollbar = ttk.Scrollbar(
        modrinth_tree_frame, orient="vertical", command=modrinth_tree.yview
    )
    modrinth_tree.configure(yscrollcommand=modrinth_scrollbar.set)

    modrinth_tree.pack(side="left", fill="both", expand=True)
    modrinth_scrollbar.pack(side="right", fill="y")

    # === Выбранные моды ===
    selected_frame = ttk.LabelFrame(main_frame, text="✅ Выбранные моды", padding=10)
    selected_frame.pack(fill="x", pady=(0, 20))

    selected_tree = ttk.Treeview(
        selected_frame, columns=("source", "name", "file"), show="headings", height=4
    )
    selected_tree.heading("source", text="Источник")
    selected_tree.heading("name", text="Название")
    selected_tree.heading("file", text="Файл")

    selected_tree.column("source", width=80)
    selected_tree.column("name", width=250)
    selected_tree.column("file", width=200)

    selected_scrollbar = ttk.Scrollbar(
        selected_frame, orient="vertical", command=selected_tree.yview
    )
    selected_tree.configure(yscrollcommand=selected_scrollbar.set)

    selected_tree.pack(side="left", fill="both", expand=True)
    selected_scrollbar.pack(side="right", fill="y")

    # === Управление модами ===
    def on_mod_select(event):
        selection = modrinth_tree.selection()
        if not selection:
            return

        item = modrinth_tree.item(selection[0])
        tags = item["tags"]
        if not tags:
            return

        mod_id = tags[0]  # ✅ project_id
        mod_title = item["values"][0].split(" (")[0]

        if not hasattr(collection_window, "last_search_results"):
            return

        matching_mod = next((m for m in collection_window.last_search_results if m["title"] == mod_title), None)
        if not matching_mod:
            return

        if matching_mod.get("compatible"):
            return  # ✅ Не показываем, если совместим

        # Теперь можно безопасно использовать mod_id
        try:
            # Получаем ВСЕ версии мода, чтобы показать пользователю
            all_versions_response = api.session.get(
                f"https://api.modrinth.com/v2/project/{mod_id}/version",
                timeout=10
            )
            if not all_versions_response.ok:
                messagebox.showwarning("Ошибка", "Не удалось загрузить данные о моде", parent=collection_window)
                return

            all_versions = all_versions_response.json()

            # Собираем данные
            game_versions = set()
            loaders = set()
            latest_version = None

            for v in all_versions:
                if v.get("game_versions"):
                    game_versions.update(v["game_versions"])
                if v.get("loaders"):
                    loaders.update([l.lower() for l in v["loaders"]])
                if not latest_version and v.get("version_number"):
                    latest_version = v["version_number"]

            game_versions = sorted(game_versions, key=lambda x: [int(p) if p.isdigit() else p for p in x.split(".")],
                                   reverse=True)
            loaders = sorted(loaders)

            message = f"❌ Мод '{mod_title}' не совместим:\n\n"
            message += f"• Версия: {version_var.get()}\n"
            message += f"• Загрузчик: {loader_var.get()}\n\n"

            if latest_version:
                message += f"📦 Последняя версия: {latest_version}\n"
            if game_versions:
                message += f"🟢 Поддерживаемые MC: {', '.join(game_versions[:5])}...\n"
            if loaders:
                message += f"🔧 Поддерживаемые: {', '.join(loaders)}\n"

            messagebox.showinfo("Совместимость", message, parent=collection_window)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить данные:\n{e}", parent=collection_window)
    selected_buttons = ttk.Frame(selected_frame)
    selected_buttons.pack(fill="x", pady=(10, 0))
    modrinth_tree.bind("<<TreeviewSelect>>", on_mod_select)

    def add_selected_mods():

        current_tab = notebook.index(notebook.select())
        if current_tab == 1:  # Modrinth
            for item in modrinth_tree.selection():
                values = modrinth_tree.item(item)["values"]
                tags = modrinth_tree.item(item)["tags"]  # → (project_id, filename)

                if len(tags) < 2:
                    continue

                mod_id = tags[0]  # ✅ строка: project_id
                filename = tags[1]  # ✅ строка: filename

                mod_title = values[0].split(" (")[0]

                if not any(selected_tree.item(i)["values"][1] == mod_title for i in selected_tree.get_children()):
                    selected_tree.insert(
                        "", "end",
                        values=("Modrinth", mod_title, filename),
                        tags=("modrinth", mod_id, filename)
                    )
    def remove_selected_mods():
        for item in selected_tree.selection():
            selected_tree.delete(item)

    def clear_all_mods():
        if selected_tree.get_children() and messagebox.askyesno("Подтверждение", "Очистить все выбранные моды?"):
            selected_tree.delete(*selected_tree.get_children())

    ttk.Button(selected_buttons, text="➕ Добавить выбранные", command=add_selected_mods, width=18).pack(side="left", padx=5)
    ttk.Button(selected_buttons, text="🗑️ Удалить выбранные", command=remove_selected_mods, width=18).pack(side="left", padx=5)
    ttk.Button(selected_buttons, text="🗑️ Очистить все", command=clear_all_mods, width=15).pack(side="left", padx=5)

    # === Создание сборки ===
    def create_collection():
        name = name_var.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Введите название сборки!")
            return

        mods = []
        failed_mods = []

        progress_window = tk.Toplevel(collection_window)
        set_window_icon(progress_window)
        progress_window.title("Обработка модов")
        progress_window.geometry("500x300")
        progress_window.transient(collection_window)
        progress_window.grab_set()

        ttk.Label(progress_window, text="Получение информации о модах...", font=("Comfortaa", 12)).pack(pady=10)
        progress = ttk.Progressbar(progress_window, orient="horizontal", mode="determinate")
        progress.pack(fill="x", padx=20, pady=10)

        status_var = tk.StringVar(value="Подготовка...")
        status_label = ttk.Label(progress_window, textvariable=status_var)
        status_label.pack()

        log_text = tk.Text(progress_window, height=10, width=60)
        log_text.pack(fill="both", expand=True, padx=20, pady=10)

        def process_mods_thread():
            total_mods = len(selected_tree.get_children())
            for i, item in enumerate(selected_tree.get_children()):
                values = selected_tree.item(item)["values"]
                tags = selected_tree.item(item)["tags"]

                progress_window.after(0, lambda idx=i: progress.config(value=(idx * 100) // total_mods))
                progress_window.after(0, lambda v=values: status_var.set(f"Обработка: {v[1]}"))

                mod_info = {"source": tags[0], "name": values[1], "filename": values[2]}

                if tags[0] == "local":
                    log_text.insert("end", f"🔍 Ищем на Modrinth: {values[1]}...\n")
                    log_text.see("end")
                    modrinth_info = find_mod_on_modrinth(api, values[1], version_var.get(), loader_var.get())
                    if modrinth_info:
                        mod_info.update({
                            "source": "modrinth",
                            "modrinth_id": modrinth_info["id"],
                            "modrinth_slug": modrinth_info["slug"],
                            "correct_filename": modrinth_info["filename"],
                        })
                        mods.append(mod_info)
                        log_text.insert("end", f"✅ Найден: {modrinth_info['title']}\n")
                    else:
                        failed_mods.append(values[1])
                        log_text.insert("end", f"❌ Не найден на Modrinth: {values[1]}\n")
                elif tags[0] == "modrinth":
                    mod_info["modrinth_id"] = tags[1]
                    mods.append(mod_info)
                    log_text.insert("end", f"✅ Modrinth мод: {values[1]}\n")

                log_text.see("end")

            progress_window.after(0, progress_window.destroy)
            progress_window.after(0, lambda: finalize_collection_creation(name, mods, failed_mods))

        def finalize_collection_creation(name, mods, failed_mods):
            if not mods:
                messagebox.showerror("Ошибка", "Не удалось найти ни одного мода на Modrinth!")
                return

            if failed_mods:
                messagebox.showwarning(
                    "Внимание",
                    f"Следующие моды не найдены на Modrinth и будут пропущены:\n" + "\n".join(failed_mods),
                )

            collection_data = {
                "name": name,
                "minecraft_version": version_var.get(),
                "loader": loader_var.get(),
                "created_at": dt.now().isoformat(),
                "mods": mods,
                "mod_count": len(mods),
            }

            safe_name = "".join(c for c in name if c not in '/\\:*?"<>|')
            filename = f"{safe_name}.json"
            filepath = os.path.join(COLLECTIONS_CONFIG["collections_dir"], filename)

            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(collection_data, f, indent=2, ensure_ascii=False)
                message = f"Сборка '{name}' создана!\n\n• Модов: {len(mods)}\n• Версия: {version_var.get()}\n• Загрузчик: {loader_var.get()}"
                if failed_mods:
                    message += f"\n• Пропущено: {len(failed_mods)}"
                messagebox.showinfo("Успех", message)
                collection_window.destroy()
                show_collection_manager()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать сборку: {e}")

        threading.Thread(target=process_mods_thread, daemon=True).start()

    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x")
    ttk.Button(button_frame, text="✅ Создать сборку", command=create_collection).pack(side="left", padx=5)
    ttk.Button(button_frame, text="❌ Отмена", command=collection_window.destroy).pack(side="right", padx=5)

def find_mod_on_modrinth(api, mod_name, minecraft_version, loader):
    """Улучшенный поиск модов на Modrinth"""
    try:
        print(f"🔍 Улучшенный поиск: '{mod_name}' для {minecraft_version} {loader}")

        # Более агрессивная очистка названия
        clean_name = aggressive_clean_name(mod_name)
        print(f"🧹 Очищенное название: '{clean_name}'")

        # Расширенный список поисковых запросов
        search_queries = generate_search_queries(mod_name, clean_name)
        print(f"📋 Запросы поиска: {search_queries[:5]}")  # Показываем первые 5

        # Пробуем найти по точному названию файла
        exact_match = try_find_by_filename(api, mod_name, minecraft_version, loader)
        if exact_match:
            return exact_match

        # Поиск по всем запросам
        for query in search_queries:
            if not query or len(query) < 10:
                continue

            print(f"🔎 Ищем: '{query}'")
            results = api.search_mods(query, limit=20)

            if not results or "hits" not in results or not results["hits"]:
                continue

            print(f"📦 Найдено результатов: {len(results['hits'])}")

            # Проверяем все результаты
            best_match = find_best_match(
                results["hits"], mod_name, clean_name, minecraft_version, loader, api
            )
            if best_match:
                return best_match

        # Последняя попытка: поиск по ключевым словам
        return try_keyword_search(api, mod_name, minecraft_version, loader)

    except Exception as e:
        print(f"💥 Ошибка поиска мода {mod_name}: {e}")
        return None


def aggressive_clean_name(mod_name):
    """Более агрессивная очистка названия мода"""
    import re

    # Удаляем версии, загрузчики и другие мусорные слова
    patterns_to_remove = [
        r"[\d\.\-_]+(?:fabric|forge|quilt|neoforge|mc|minecraft)",
        r"\b(?:fabric|forge|quilt|neoforge|mc|minecraft|mod|jar)\b",
        r"[\(\\)\[\]\{\}]",
        r"\s+",
    ]

    cleaned = mod_name.lower()
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)

    # Удаляем лишние пробелы и возвращаем
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Если после очистки ничего не осталось, используем оригинал
    return cleaned if cleaned else mod_name.lower()


def generate_search_queries(original_name, clean_name):
    """Генерирует расширенный список поисковых запросов"""
    queries = set()

    # Добавляем различные варианты
    variants = [
        clean_name,
        original_name,
        clean_name.replace(" ", ""),
        clean_name.replace(" ", "-"),
        clean_name.replace(" ", "_"),
        extract_core_name(original_name),
        remove_version_info(original_name),
        get_acronym(clean_name),
    ]

    # Добавляем отдельные слова из названия
    words = clean_name.split()
    for word in words:
        if len(word) > 3 and not word.isdigit():
            queries.add(word)

    # Добавляем комбинации слов
    if len(words) > 1:
        queries.add(" ".join(words[:2]))  # Первые два слова
        queries.add(" ".join(words[-2:]))  # Последние два слова

    # Фильтруем и возвращаем
    return [q for q in variants if q and len(q) > 1]


def extract_core_name(mod_name):
    """Извлекает ядро названия мода"""
    # Удаляем все, что выглядит как версия
    import re

    core = re.sub(r"[\d.\-_]+.*$", "", mod_name)
    return core.strip()


def remove_version_info(mod_name):
    """Удаляет информацию о версии"""
    import re

    # Удаляем паттерны версий типа 1.2.3, 1.2.3+1.20.1 и т.д.
    cleaned = re.sub(r"[\d.\-_]+\+?[\d.\-_]*", "", mod_name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def get_acronym(mod_name):
    """Создает акроним из названия"""
    words = mod_name.split()
    if len(words) > 1:
        return "".join(word[0].upper() for word in words if word)
    return ""


def try_find_by_filename(api, filename, minecraft_version, loader):
    """Пытается найти мод по точному имени файла"""
    try:
        # Извлекаем название из имени файла (без .jar и версии)
        base_name = filename.replace(".jar", "")

        # Удаляем информацию о версии и загрузчике
        clean_file_name = re.sub(r"[\d.\-_]+(?:fabric|forge|quilt|neoforge).*$", "", base_name)
        clean_file_name = re.sub(r"\s+", " ", clean_file_name).strip()

        if len(clean_file_name) > 3:
            print(f"📁 Поиск по имени файла: '{clean_file_name}'")
            results = api.search_mods(clean_file_name, limit=10)

            if results and "hits" in results and results["hits"]:
                for mod in results["hits"]:
                    similarity = calculate_similarity(
                        mod["title"].lower(), clean_file_name.lower()
                    )
                    if similarity > 0.4:
                        versions = api.get_mod_versions(
                            mod["project_id"], minecraft_version, loader.lower()
                        )
                        if versions:
                            latest_version = versions[0]
                            file = latest_version["files"][0]
                            print(f"✅ Найден по имени файла: {mod['title']}")
                            return {
                                "id": mod["project_id"],
                                "slug": mod["slug"],
                                "title": mod["title"],
                                "filename": file["filename"],
                            }
    except Exception as e:
        print(f"⚠️ Ошибка поиска по файлу: {e}")

    return None


def find_best_match(mods, original_name, clean_name, minecraft_version, loader, api):
    """Находит лучший совпадающий мод"""
    best_similarity = 0
    best_mod = None

    for mod in mods:
        mod_title = mod["title"].lower()

        # Вычисляем несколько метрик схожести
        similarity1 = calculate_similarity(mod_title, original_name.lower())
        similarity2 = calculate_similarity(mod_title, clean_name)
        similarity3 = calculate_word_overlap(mod_title, clean_name)

        # Общая схожесть (максимум из всех метрик)
        total_similarity = max(similarity1, similarity2, similarity3)

        print(f"  📊 '{mod['title']}' - схожесть: {total_similarity:.2f}")

        if total_similarity > best_similarity:
            # Проверяем поддержку версии
            versions = api.get_mod_versions(
                mod["project_id"], minecraft_version, loader.lower()
            )
            if versions:
                best_similarity = total_similarity
                latest_version = versions[0]
                file = latest_version["files"][0]
                best_mod = {
                    "id": mod["project_id"],
                    "slug": mod["slug"],
                    "title": mod["title"],
                    "filename": file["filename"],
                }

    # Понижаем порог для принятия решения
    if best_mod and best_similarity > 0.2:  # Был 0.6
        print(
            f"✅ Лучшее совпадение: {best_mod['title']} (схожесть: {best_similarity:.2f})"
        )
        return best_mod

    return None


def calculate_word_overlap(str1, str2):
    """Вычисляет пересечение слов между строками"""
    words1 = set(str1.lower().split())
    words2 = set(str2.lower().split())

    if not words1 or not words2:
        return 0.0

    common_words = words1.intersection(words2)
    return len(common_words) / min(len(words1), len(words2))


def try_keyword_search(api, mod_name, minecraft_version, loader):
    """Поиск по ключевым словам когда точный поиск не сработал"""
    print(f"🔍 Переходим к поиску по ключевым словам: {mod_name}")

    # Ключевые слова для специфичных модов
    keyword_map = {
        "appliedenergistics": "applied energistics 2",
        "xaeros": "xaero",
        "inventoryprofiles": "inventory profiles next",
        "travelersbackpack": "traveler backpack",
        "lambdynamiclights": "lamb dynamic lights",
        "fallingleaves": "falling leaves",
        "ironchests": "iron chests",
        "techreborn": "tech reborn",
        "reborncore": "reborn core",
        "mavapi": "more axolotl variants api",
        "mavm": "more axolotl variants mod",
        "noindium": "no indium",
    }

    # Проверяем по ключевым словам
    for key, search_term in keyword_map.items():
        if key in mod_name.lower():
            print(f"🔑 Используем ключевое слово: {search_term}")
            results = api.search_mods(search_term, limit=5)

            if results and "hits" in results and results["hits"]:
                mod = results["hits"][0]
                versions = api.get_mod_versions(
                    mod["project_id"], minecraft_version, loader.lower()
                )
                if versions:
                    latest_version = versions[0]
                    file = latest_version["files"][0]
                    print(f"✅ Найден по ключевому слову: {mod['title']}")
                    return {
                        "id": mod["project_id"],
                        "slug": mod["slug"],
                        "title": mod["title"],
                        "filename": file["filename"],
                    }

    return None


MANUAL_MOD_MAPPINGS = {
    "appliedenergistics2 fabric 15.4.9": "ae2",
    "xaeros minimap 25.2.10 fabric 1.20": "xaeros-minimap",
    "xaerosworldmap 1.39.12 fabric 1.20": "xaeros-world-map",
    "travelersbackpack fabric 1.20.1 9.1.41": "travelers-backpack",
    "ironchests 5.0.2 fabric": "iron-chests",
    "fallingleaves 1.15.6+1.20.1": "falling-leaves",
    "lambdynamiclights 4.4.0+1.20.1": "lambdynamiclights",
    "techreborn 5.8.3": "techreborn",
    "reborncore 5.8.3": "reborn-core",
    "inventoryprofilesnext fabric 1.20 1.10.19": "inventory-profiles-next",
    "noindium 1.1.0+1.20": "no-indium",
    "mavapi 1.1.4 mc1.20.1": "more-axolotl-variants-api",
    "mavm 1.2.6 mc1.20.1": "more-axolotl-variants-mod",
}


def try_manual_mapping(api, mod_name, minecraft_version, loader):
    """Пробует найти мод по ручным сопоставлениям"""
    clean_mod_name = mod_name.lower().strip()

    for key, slug in MANUAL_MOD_MAPPINGS.items():
        if key in clean_mod_name:
            print(f"🔧 Используем ручное сопоставление: {slug}")
            try:
                # Прямой запрос к API по slug
                project_url = f"{api.base_url}/project/{slug}"
                response = api.session.get(project_url)

                if response.status_code == 200:
                    project_data = response.json()
                    versions = api.get_mod_versions(
                        project_data["id"], minecraft_version, loader.lower()
                    )
                    if versions:
                        latest_version = versions[0]
                        file = latest_version["files"][0]
                        print(
                            f"✅ Найден через ручное сопоставление: {project_data['title']}"
                        )
                        return {
                            "id": project_data["id"],
                            "slug": project_data["slug"],
                            "title": project_data["title"],
                            "filename": file["filename"],
                        }
            except Exception as e:
                print(f"⚠️ Ошибка ручного сопоставления: {e}")

    return None


def clean_mod_name(mod_name):
    """Очищает название мода от версий и лишних частей"""
    # Удаляем версии типа 1.20.1, 1.19.2 и т.д.
    import re

    cleaned = re.sub(
        r"[\d.\-_]+(?:fabric|forge|quilt|neoforge)?", " ", mod_name, flags=re.IGNORECASE
    )
    cleaned = re.sub(
        r"\b(?:fabric|forge|quilt|neoforge|mc|minecraft|mod)\b",
        " ",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Если после очистки ничего не осталось, возвращаем оригинал
    return cleaned if cleaned else mod_name


def extract_main_words(mod_name):
    """Извлекает основные слова из названия"""
    words = mod_name.split()
    # Оставляем только слова длиной > 3 символов и не являющиеся версиями
    main_words = [
        word for word in words if len(word) > 3 and not re.match(r"^[\d.\-_]+$", word)
    ]
    return " ".join(main_words[:3])  # Берем до 3 слов


def calculate_similarity(str1, str2):
    """Вычисляет схожесть между двумя строками"""
    # Простой алгоритм схожести
    str1, str2 = str1.lower(), str2.lower()

    # Если одна строка содержится в другой
    if str1 in str2 or str2 in str1:
        return 0.8

    # Считаем совпадающие слова
    words1 = set(str1.split())
    words2 = set(str2.split())

    if not words1 or not words2:
        return 0.0

    common_words = words1.intersection(words2)
    similarity = len(common_words) / max(len(words1), len(words2))

    return similarity


COLLECTIONS_CONFIG = {
    "collections_dir": os.path.join(
        os.path.expanduser("~"), "YamalPixel", "collections"
    )
}


# Функция показа менеджера сборок
def show_collection_manager():
    manager_window = tk.Toplevel(win)
    set_window_icon(manager_window)
    manager_window.title("Менеджер сборок (Бета)")
    manager_window.geometry("1000x500")
    manager_window.transient(win)
    manager_window.grab_set()

    main_frame = ttk.Frame(manager_window, padding=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(
        main_frame, text="📦 Менеджер сборок модов", font=("Comfortaa", 16, "bold")
    ).pack(pady=(0, 20))

    # Информация о папке
    collections_dir = COLLECTIONS_CONFIG["collections_dir"]
    info_label = ttk.Label(
        main_frame, text=f"Папка: {collections_dir}", foreground="gray"
    )
    info_label.pack(pady=(0, 10))

    # Список сборок
    tree = ttk.Treeview(
        main_frame,
        columns=("name", "version", "loader", "mods", "created"),
        show="headings",
    )
    tree.heading("name", text="Название")
    tree.heading("version", text="Версия")
    tree.heading("loader", text="Загрузчик")
    tree.heading("mods", text="Модов")
    tree.heading("created", text="Создана")

    tree.column("name", width=200)
    tree.column("version", width=100)
    tree.column("loader", width=80)
    tree.column("mods", width=60)
    tree.column("created", width=100)

    # Статус сборок
    status_var = tk.StringVar(value="Загрузка...")
    status_label = ttk.Label(main_frame, textvariable=status_var, foreground="blue")
    status_label.pack(pady=5)

    def load_collections():
        tree.delete(*tree.get_children())
        collections_dir = COLLECTIONS_CONFIG["collections_dir"]

        if not os.path.exists(collections_dir):
            status_var.set("Папка сборок не существует!")
            return

        try:
            files = os.listdir(collections_dir)
            json_files = [f for f in files if f.endswith(".json")]
            status_var.set(f"Найдено сборок: {len(json_files)}")

            for file in json_files:
                filepath = os.path.join(collections_dir, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    # Проверяем структуру данных
                    if all(
                            field in data
                            for field in [
                                "name",
                                "minecraft_version",
                                "loader",
                                "mod_count",
                                "created_at",
                            ]
                    ):
                        created = datetime.datetime.fromisoformat(
                            data["created_at"]
                        ).strftime("%d.%m.%Y")
                        tree.insert(
                            "",
                            "end",
                            values=(
                                data["name"],
                                data["minecraft_version"],
                                data["loader"],
                                data["mod_count"],
                                created,
                            ),
                            tags=(file,),
                        )
                    else:
                        print(f"Неполные данные в файле {file}")

                except Exception as e:
                    print(f"Ошибка загрузки {file}: {e}")

        except Exception as e:
            status_var.set(f"Ошибка: {e}")

    tree.pack(fill="both", expand=True)
    load_collections()

    # Кнопки управления
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=10)

    def refresh_collections():
        status_var.set("Обновление...")
        load_collections()

    def open_collections_folder():
        os.makedirs(COLLECTIONS_CONFIG["collections_dir"], exist_ok=True)
        if os.name == "nt":
            os.startfile(COLLECTIONS_CONFIG["collections_dir"])
        else:
            subprocess.Popen(["xdg-open", COLLECTIONS_CONFIG["collections_dir"]])

    def load_to_game():
        selection = tree.selection()
        if selection:
            filename = tree.item(selection[0])["tags"][0]
            load_collection_to_game(filename)
        else:
            messagebox.showwarning("Выбор", "Выберите сборку для загрузки")

    def delete_collection():
        selection = tree.selection()
        if selection:
            filename = tree.item(selection[0])["tags"][0]
            filepath = os.path.join(COLLECTIONS_CONFIG["collections_dir"], filename)
            if messagebox.askyesno("Подтверждение", "Удалить сборку?"):
                try:
                    os.remove(filepath)
                    load_collections()
                    messagebox.showinfo("Успех", "Сборка удалена")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")

    ttk.Button(button_frame, text="🔄 Обновить", command=refresh_collections).pack(
        side="left", padx=5
    )
    ttk.Button(
        button_frame, text="📁 Открыть папку", command=open_collections_folder
    ).pack(side="left", padx=5)
    ttk.Button(button_frame, text="🎮 Загрузить в игру", command=load_to_game).pack(
        side="left", padx=5
    )
    ttk.Button(button_frame, text="🗑️ Удалить", command=delete_collection).pack(
        side="left", padx=5
    )
    ttk.Button(
        button_frame,
        text="➕ Новая сборка",
        command=lambda: (manager_window.destroy(), create_new_collection()),
    ).pack(side="right", padx=5)
    ttk.Button(button_frame, text="❌ Закрыть", command=manager_window.destroy).pack(
        side="right", padx=5
    )


# Функция загрузки сборки в игру
def load_collection_to_game(filename):
    filepath = os.path.join(COLLECTIONS_CONFIG["collections_dir"], filename)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            collection = json.load(f)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить сборку: {e}")
        return

    # Создаем окно прогресса с логом
    progress_window = tk.Toplevel(win)
    set_window_icon(progress_window)
    progress_window.title(f"Загрузка сборки: {collection['name']}")
    progress_window.geometry("700x500")
    progress_window.transient(win)
    progress_window.grab_set()

    main_frame = ttk.Frame(progress_window, padding=15)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(
        main_frame,
        text=f"📦 Загрузка сборки: {collection['name']}",
        font=("Comfortaa", 14, "bold"),
    ).pack(pady=(0, 10))

    # Информация о сборке
    info_text = f"Версия: {collection['minecraft_version']} | Загрузчик: {collection['loader']} | Модов: {collection['mod_count']}"
    ttk.Label(main_frame, text=info_text).pack(pady=(0, 15))

    # Прогресс-бар
    progress = ttk.Progressbar(
        main_frame, orient="horizontal", length=600, mode="determinate"
    )
    progress.pack(fill="x", pady=5)

    # Статус и счетчик
    status_frame = ttk.Frame(main_frame)
    status_frame.pack(fill="x", pady=5)

    status_var = tk.StringVar(value="Подготовка...")
    status_label = ttk.Label(
        status_frame, textvariable=status_var, font=("Comfortaa", 10)
    )
    status_label.pack(side="left")

    counter_var = tk.StringVar(value="0/0")
    counter_label = ttk.Label(
        status_frame, textvariable=counter_var, font=("Comfortaa", 10)
    )
    counter_label.pack(side="right")

    # Детальный лог
    log_frame = ttk.LabelFrame(main_frame, text="Детальный лог загрузки", padding=10)
    log_frame.pack(fill="both", expand=True, pady=(10, 0))

    log_text = tk.Text(log_frame, height=15, width=80, font=("Consolas", 9))
    log_scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=log_text.yview)
    log_text.configure(yscrollcommand=log_scrollbar.set)

    log_text.pack(side="left", fill="both", expand=True)
    log_scrollbar.pack(side="right", fill="y")

    def log_message(message):
        win.after(0, lambda: log_text.insert("end", f"{message}\n"))
        win.after(0, lambda: log_text.see("end"))

    def download_thread():
        import concurrent.futures
        mods_dir = os.path.join(CONFIG["minecraft_dir"], "mods")
        os.makedirs(mods_dir, exist_ok=True)

        log_message(f"📁 Папка модов: {mods_dir}")
        log_message(f"🔄 Начинаем загрузку {len(collection['mods'])} модов...")

        # Бэкап и очистка
        backup_path = create_mods_backup(collection["name"])
        if backup_path:
            log_message(f"📂 Создан бэкап: {os.path.basename(backup_path)}")

        cleared_count = clear_mods_directory(mods_dir)
        log_message(f"🗑️ Очищено модов: {cleared_count}")

        # Подготовка
        api = ModrinthAPI()
        total_mods = len(collection["mods"])
        success_count = 0

        # Прогресс
        progress["maximum"] = total_mods

        # Функция загрузки одного мода
        def download_single_mod(mod):
            nonlocal success_count
            try:
                log_message(f"\n🔍 Мод: {mod['name']}")

                if mod["source"] != "modrinth":
                    log_message(f"   ⚠️  Источник не поддерживается: {mod['source']}")
                    return False

                versions = api.get_mod_versions(
                    mod_id=mod["modrinth_id"],
                    minecraft_version=collection["minecraft_version"],
                    loader=collection["loader"].lower(),
                )

                if not versions:
                    log_message("   ❌ Не найдены совместимые версии")
                    return False

                latest_version = versions[0]
                version_id = latest_version["id"]
                project_slug = mod.get("modrinth_slug", mod["modrinth_id"])

                # Ищем JAR-файл
                target_file = next(
                    (f for f in latest_version["files"] if f["filename"].endswith(".jar")),
                    latest_version["files"][0] if latest_version["files"] else None
                )

                if not target_file:
                    log_message("   ❌ Нет файла для скачивания")
                    return False

                filename = target_file["filename"]
                filepath = os.path.join(mods_dir, filename)

                log_message(f"   ⬇️  {filename}")

                # Пробуем скачать
                if api.download_mod(project_slug, version_id, filename, mods_dir):
                    log_message(f"   ✅ Успешно: {filename}")
                    return True
                else:
                    log_message(f"   ❌ Ошибка: {filename}")
                    return False

            except Exception as e:
                log_message(f"   💥 Ошибка: {e}")
                return False

        # Параллельная загрузка
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(download_single_mod, mod) for mod in collection["mods"]]
            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    success_count += 1
                win.after(0, lambda: progress.step(1))
                win.after(0, lambda s=success_count: counter_var.set(f"{s}/{total_mods}"))

        # Завершение
        log_message(f"\n🎉 ЗАВЕРШЕНО! Успешно: {success_count}/{total_mods}")
        win.after(0, lambda: finish_loading(progress_window, collection, success_count, total_mods, backup_path))

    threading.Thread(target=download_thread, daemon=True).start()




def create_mods_backup(collection_name):
    """Создание бэкапа модов"""
    mods_dir = os.path.join(CONFIG["minecraft_dir"], "mods")
    backup_dir = os.path.join(CONFIG["minecraft_dir"], "mods_backup")
    os.makedirs(backup_dir, exist_ok=True)

    if os.path.exists(mods_dir) and any(
            f.endswith(".jar") for f in os.listdir(mods_dir)
    ):
        timestamp = dt.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{collection_name}_{timestamp}"
        backup_path = os.path.join(backup_dir, backup_name)
        try:
            shutil.copytree(mods_dir, backup_path)
            return backup_path
        except Exception as e:
            print(f"Ошибка бэкапа: {e}")
    return None


def clear_mods_directory(mods_dir):
    """Очистка папки модов"""
    count = 0
    if os.path.exists(mods_dir):
        for file in os.listdir(mods_dir):
            if file.endswith(".jar"):
                try:
                    os.remove(os.path.join(mods_dir, file))
                    count += 1
                except Exception as e:
                    print(f"Не удалось удалить {file}: {e}")
    return count


def handle_local_mod(mod, mods_dir):
    """Обработка локального мода"""
    # Пробуем найти файл в нескольких местах
    possible_paths = [
        os.path.join(CONFIG["minecraft_dir"], "mods", mod["filename"]),
        os.path.join(COLLECTIONS_CONFIG["collections_dir"], "mods", mod["filename"]),
        os.path.join(os.path.dirname(CONFIG["minecraft_dir"]), "mods", mod["filename"]),
    ]

    for src_path in possible_paths:
        if os.path.exists(src_path):
            try:
                shutil.copy2(src_path, os.path.join(mods_dir, mod["filename"]))
                return True
            except Exception as e:
                print(f"Ошибка копирования {src_path}: {e}")

    print(f"Локальный файл не найден: {mod['filename']}")
    return False


def handle_modrinth_mod(mod, collection, api, mods_dir, minecraft_version, loader_type, log_callback):
    """Обработка мода с Modrinth с правильным скачиванием"""
    try:
        log_callback(f"🔍 Получаем информацию о {mod['name']}...")

        versions = api.get_mod_versions(
            mod_id=mod["project_id"],
            minecraft_version=minecraft_version,
            loader=loader_type
        )

        if not versions:
            log_callback(f"❌ Не найдены версии для {mod['name']}")
            return False

        # Выбираем последнюю версию
        latest_version = versions[0]
        version_id = latest_version["id"]

        if "files" not in latest_version or not latest_version["files"]:
            log_callback(f"❌ Нет информации о файлах для {mod['name']}")
            return False

        file_info = latest_version["files"][0]
        filename = file_info["filename"]

        # Получаем slug проекта для скачивания
        project_slug = mod.get("modrinth_slug") or mod["modrinth_id"]

        log_callback(f"📥 Скачиваем {filename}...")
        log_callback(f"🆔 Version ID: {version_id}")
        log_callback(f"🔗 Project: {project_slug}")

        # Скачиваем мод
        if api.download_mod(project_slug, version_id, filename, mods_dir):
            log_callback(f"✅ Успешно скачан: {filename}")
            return True
        else:
            # Пробуем через прямой URL из file_info
            if "url" in file_info and file_info["url"]:
                log_callback(f"🔄 Пробуем прямую ссылку...")
                direct_url = file_info["url"]
                try:
                    response = api.session.get(direct_url, timeout=30, stream=True)
                    response.raise_for_status()

                    filepath = os.path.join(mods_dir, filename)
                    with open(filepath, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                    log_callback(f"✅ Успешно скачан (прямая ссылка): {filename}")
                    return True
                except Exception as e:
                    log_callback(f"❌ Ошибка прямой ссылки: {str(e)}")

            log_callback(f"❌ Не удалось скачать: {filename}")
            return False

    except Exception as e:
        log_callback(f"💥 Критическая ошибка {mod['name']}: {str(e)}")
        return False


def finish_loading(progress_window, collection, success_count, total_mods, backup_path):
    """Завершение загрузки"""
    progress_window.destroy()

    message = (
        f"Сборка '{collection['name']}' загружена!\n\n"
        f"✅ Успешно: {success_count}/{total_mods} модов"
    )

    if backup_path:
        message += f"\n\n📂 Бэкап создан: {os.path.basename(backup_path)}"

    if success_count < total_mods:
        message += (
            "\n\n⚠️ Некоторые моды не удалось загрузить. Проверьте лог для деталей."
        )

    messagebox.showinfo("Загрузка завершена", message)