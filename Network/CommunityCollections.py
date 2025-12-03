"""
Модуль для работы с общедоступными сборками на сервере
"""
import requests
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
import time

# Конфигурация сервера (замените на реальный адрес вашего сервера)
COMMUNITY_SERVER_URL = "http://90.151.59.120:8000"  # Пример адреса
SERVER_API_KEY = "YAMALPIXEL_COMMUNITY"


class CommunityCollectionAPI:
    """API для работы с общедоступными сборками"""

    def __init__(self):
        self.base_url = COMMUNITY_SERVER_URL
        self.headers = {
            "X-API-Key": SERVER_API_KEY,
            "Content-Type": "application/json"
        }
        self.timeout = 30

    def test_connection(self):
        """Проверка подключения к серверу"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/community/ping",
                timeout=10,
                headers=self.headers
            )
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ошибка подключения к серверу сборок: {e}")
            return False

    def get_community_collections(self, page=1, limit=20, category="all"):
        """Получение списка общедоступных сборок"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/community/collections",
                params={
                    "page": page,
                    "limit": limit,
                    "category": category,
                    "sort_by": "downloads"
                },
                timeout=self.timeout,
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Ошибка получения сборок: {response.status_code}")
                return {"success": False, "error": f"Ошибка сервера: {response.status_code}"}

        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
            return {"success": False, "error": str(e)}

    def get_collection_details(self, collection_id):
        """Получение деталей конкретной сборки"""
        try:
            print(f"🔍 [DEBUG] Запрос деталей сборки ID={collection_id}")

            response = requests.get(
                f"{self.base_url}/api/v1/community/collection/{collection_id}",
                timeout=self.timeout,
                headers=self.headers
            )

            print(f"🔍 [DEBUG] Статус: {response.status_code}")
            print(f"🔍 [DEBUG] Ответ: {response.text[:200] if response.text else 'Пустой ответ'}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"🔍 [DEBUG] JSON успешно распарсен: {data.get('success', False)}")
                    return data
                except json.JSONDecodeError as e:
                    print(f"🔍 [DEBUG] Ошибка парсинга JSON: {e}")
                    return {"success": False, "error": f"Invalid JSON response"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            print(f"🔍 [DEBUG] Исключение: {e}")
            return {"success": False, "error": str(e)}

    def upload_collection(self, collection_data, username="anonymous"):
        """Загрузка сборки на сервер"""
        try:
            # Добавляем метаданные
            collection_data["uploader"] = username
            collection_data["upload_date"] = datetime.now().isoformat()
            collection_data["downloads"] = 0

            response = requests.post(
                f"{self.base_url}/api/v1/community/upload",
                json=collection_data,
                timeout=self.timeout,
                headers=self.headers
            )

            if response.status_code == 200:
                result = response.json()
                return result
            else:
                return {"success": False, "error": f"Ошибка загрузки: {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_collections(self, query, page=1, limit=20):
        """Поиск сборок по запросу"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/community/search",
                params={
                    "q": query,
                    "page": page,
                    "limit": limit
                },
                timeout=self.timeout,
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"success": False, "error": f"Ошибка поиска: {response.status_code}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def download_collection(self, collection_id):
        """Скачивание сборки с сервера"""
        try:
            print(f"🔍 [DEBUG] Скачивание сборки ID={collection_id}")
            print(f"🔍 [DEBUG] URL={self.base_url}/api/v1/community/download/{collection_id}")

            response = requests.get(
                f"{self.base_url}/api/v1/community/download/{collection_id}",
                timeout=self.timeout,
                headers=self.headers
            )

            print(f"🔍 [DEBUG] Статус: {response.status_code}")
            print(f"🔍 [DEBUG] Ответ (первые 300 символов): {response.text[:300] if response.text else 'Пустой ответ'}")

            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"🔍 [DEBUG] JSON успешно распарсен: {data.get('success', False)}")
                    return data
                except json.JSONDecodeError as e:
                    print(f"🔍 [DEBUG] Ошибка парсинга JSON: {e}")
                    return {"success": False, "error": f"Invalid JSON response: {response.text[:100]}"}
            else:
                print(f"🔍 [DEBUG] HTTP ошибка: {response.status_code}")
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except Exception as e:
            print(f"🔍 [DEBUG] Исключение: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def increment_downloads(self, collection_id):
        """Увеличение счетчика скачиваний"""
        try:
            # ИСПРАВЛЕННЫЙ URL - используем правильный эндпоинт для статистики
            url = f"{self.base_url}/api/v1/community/stats/download/{collection_id}"
            print(f"🔍 Увеличение счетчика: POST {url}")

            response = requests.post(
                url,
                timeout=10,
                headers=self.headers
            )

            print(f"🔍 Статус ответа: {response.status_code}")
            print(f"🔍 Текст ответа: {response.text[:100] if response.text else 'Пустой ответ'}")

            return response.status_code == 200

        except Exception as e:
            print(f"🔍 Исключение при увеличении счетчика: {e}")
            return False

    def get_collection_categories(self):
        """Получение списка категорий"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/community/categories",
                timeout=10,
                headers=self.headers
            )

            if response.status_code == 200:
                return response.json()
            return {"categories": ["Все", "Оптимизация", "Технологии", "Приключения", "Квесты", "Магия", "Биомы",
                                   "Строительство", "Выживание", "PvP"]}

        except:
            return {"categories": ["Все", "Оптимизация", "Технологии", "Приключения", "Квесты", "Магия", "Биомы",
                                   "Строительство", "Выживание", "PvP"]}


def show_community_collections(parent_window, version_selector_callback=None):
    """Показать окно с общедоступными сборками"""
    from ConfDir.Configs import COLLECTIONS_CONFIG

    api = CommunityCollectionAPI()

    # Проверка подключения
    if not api.test_connection():
        messagebox.showerror(
            "Ошибка подключения",
            "Не удалось подключиться к серверу сборок сообщества.\n\n"
            "Причины:\n"
            "• Сервер временно недоступен\n"
            "• Проверьте интернет-соединение\n"
            "• Попробуйте позже"
        )
        return

    # Создание окна
    community_window = tk.Toplevel(parent_window)
    community_window.title("📚 Сборки сообщества")
    community_window.geometry("1400x800")
    community_window.resizable(True, True)

    # Центрирование окна
    community_window.update_idletasks()
    x = (parent_window.winfo_screenwidth() // 2) - (1400 // 2)
    y = (parent_window.winfo_screenheight() // 2) - (800 // 2)
    community_window.geometry(f"1400x800+{x}+{y}")

    # Основной фрейм
    main_frame = ttk.Frame(community_window, padding=20)
    main_frame.pack(fill="both", expand=True)

    # Заголовок
    header_frame = ttk.Frame(main_frame)
    header_frame.pack(fill="x", pady=(0, 20))

    ttk.Label(
        header_frame,
        text="📚 Сборки сообщества",
        font=("Comfortaa", 20, "bold")
    ).pack(side="left")

    ttk.Label(
        header_frame,
        text="Скачивайте и делитесь сборками модов с другими игроками",
        font=("Comfortaa", 10),
        foreground="gray"
    ).pack(side="left", padx=(10, 0))

    # Панель поиска и фильтров
    filter_frame = ttk.Frame(main_frame)
    filter_frame.pack(fill="x", pady=(0, 15))

    # Поиск
    search_frame = ttk.Frame(filter_frame)
    search_frame.pack(side="left", fill="x", expand=True)

    ttk.Label(search_frame, text="Поиск:").pack(side="left")
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var, width=40)
    search_entry.pack(side="left", padx=5)

    # Категории
    ttk.Label(filter_frame, text="Категория:").pack(side="left", padx=(20, 5))
    category_var = tk.StringVar(value="Все")

    # Загружаем категории
    categories_data = api.get_collection_categories()
    if isinstance(categories_data, dict) and "categories" in categories_data:
        categories = categories_data["categories"]
    else:
        categories = ["Все", "Оптимизация", "Технологии", "Приключения", "Квесты", "Магия", "Биомы", "Строительство",
                      "Выживание", "PvP"]

    category_combo = ttk.Combobox(
        filter_frame,
        textvariable=category_var,
        values=categories,
        state="readonly",
        width=20
    )
    category_combo.pack(side="left", padx=5)

    # Сортировка
    ttk.Label(filter_frame, text="Сортировка:").pack(side="left", padx=(20, 5))
    sort_var = tk.StringVar(value="downloads")
    sort_combo = ttk.Combobox(
        filter_frame,
        textvariable=sort_var,
        values=["По популярности", "По новизне", "По имени", "По количеству модов"],
        state="readonly",
        width=20
    )
    sort_combo.pack(side="left", padx=5)

    # Кнопки фильтров
    button_frame = ttk.Frame(filter_frame)
    button_frame.pack(side="right")

    def refresh_collections():
        """Обновить список сборок"""
        load_collections_page(1)

    def search_collections():
        """Поиск сборок"""
        query = search_var.get().strip()
        if query:
            search_results = api.search_collections(query)
            display_collections(search_results)
        else:
            refresh_collections()

    ttk.Button(button_frame, text="🔍 Поиск", command=search_collections, width=10).pack(side="left", padx=2)
    ttk.Button(button_frame, text="🔄 Обновить", command=refresh_collections, width=10).pack(side="left", padx=2)
    ttk.Button(button_frame, text="📤 Загрузить свою", command=lambda: upload_collection_dialog(community_window),
               width=15).pack(side="left", padx=2)

    # Список сборок
    collections_frame = ttk.LabelFrame(main_frame, text="Доступные сборки", padding=10)
    collections_frame.pack(fill="both", expand=True)

    # Treeview для отображения сборок
    columns = ("name", "author", "version", "mods", "downloads", "rating", "updated")
    tree = ttk.Treeview(
        collections_frame,
        columns=columns,
        show="headings",
        height=15
    )

    # Настройка колонок
    tree.heading("name", text="Название сборки")
    tree.heading("author", text="Автор")
    tree.heading("version", text="Версия")
    tree.heading("mods", text="Модов")
    tree.heading("downloads", text="Скачиваний")
    tree.heading("rating", text="Рейтинг")
    tree.heading("updated", text="Обновлено")

    tree.column("name", width=300)
    tree.column("author", width=120)
    tree.column("version", width=80)
    tree.column("mods", width=80, anchor="center")
    tree.column("downloads", width=100, anchor="center")
    tree.column("rating", width=80, anchor="center")
    tree.column("updated", width=120)

    # Скроллбар
    scrollbar = ttk.Scrollbar(collections_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Пагинация
    pagination_frame = ttk.Frame(main_frame)
    pagination_frame.pack(fill="x", pady=(10, 0))

    current_page = 1
    total_pages = 1

    def update_pagination_buttons():
        """Обновить кнопки пагинации"""
        for widget in pagination_frame.winfo_children():
            widget.destroy()

        if current_page > 1:
            ttk.Button(pagination_frame, text="◀ Назад", command=lambda: load_collections_page(current_page - 1)).pack(
                side="left", padx=2)

        ttk.Label(pagination_frame, text=f"Страница {current_page} из {total_pages}").pack(side="left", padx=10)

        if current_page < total_pages:
            ttk.Button(pagination_frame, text="Вперед ▶", command=lambda: load_collections_page(current_page + 1)).pack(
                side="left", padx=2)

    def load_collections_page(page):
        """Загрузить страницу со сборками"""
        nonlocal current_page, total_pages

        # Показать индикатор загрузки
        loading_label = ttk.Label(collections_frame, text="Загрузка сборок...", font=("Comfortaa", 12))
        loading_label.place(relx=0.5, rely=0.5, anchor="center")
        community_window.update()

        try:
            category = category_var.get()
            if category == "Все":
                category_param = "all"
            else:
                category_param = category.lower()

            collections_data = api.get_community_collections(
                page=page,
                limit=20,
                category=category_param
            )

            loading_label.destroy()

            if collections_data.get("success", False):
                display_collections(collections_data)
                current_page = page
                total_pages = collections_data.get("total_pages", 1)
                update_pagination_buttons()
            else:
                error_msg = collections_data.get("error", "Неизвестная ошибка")
                messagebox.showerror("Ошибка", f"Не удалось загрузить сборки: {error_msg}")

        except Exception as e:
            loading_label.destroy()
            messagebox.showerror("Ошибка", f"Ошибка загрузки: {str(e)}")

    def display_collections(collections_data):
        """Отобразить список сборок"""
        # Очистить текущий список
        for item in tree.get_children():
            tree.delete(item)

        if "collections" not in collections_data or not collections_data["collections"]:
            tree.insert("", "end", values=("Нет сборок", "", "", "", "", "", ""))
            return

        for collection in collections_data["collections"]:
            # Форматирование даты
            updated_date = collection.get("updated_at", collection.get("upload_date", ""))
            if updated_date:
                try:
                    dt = datetime.fromisoformat(updated_date.replace('Z', '+00:00'))
                    updated_str = dt.strftime("%d.%m.%Y")
                except:
                    updated_str = updated_date[:10]
            else:
                updated_str = "Неизвестно"

            # Рейтинг в звездах
            rating = collection.get("rating", 0)
            rating_str = "★" * int(rating) + "☆" * (5 - int(rating)) if rating > 0 else "Нет оценок"

            tree.insert(
                "",
                "end",
                values=(
                    collection["name"],
                    collection.get("uploader", "Неизвестно"),
                    collection.get("minecraft_version", "1.20.1"),
                    collection.get("mod_count", 0),
                    collection.get("downloads", 0),
                    rating_str,
                    updated_str
                ),
                tags=(collection["id"],)
            )

    def on_collection_select(event):
        """Обработчик выбора сборки"""
        selection = tree.selection()
        if selection:
            collection_id = tree.item(selection[0], "tags")[0]
            show_collection_details(collection_id)

    def show_collection_details(collection_id):
        """Показать детали сборки"""
        # Создать окно деталей
        details_window = tk.Toplevel(community_window)
        details_window.title("Детали сборки")
        details_window.geometry("800x700")  # Увеличили высоту для кнопок

        # Центрирование
        details_window.update_idletasks()
        x = (community_window.winfo_screenwidth() // 2) - (800 // 2)
        y = (community_window.winfo_screenheight() // 2) - (700 // 2)
        details_window.geometry(f"800x700+{x}+{y}")

        # Загрузка данных
        details_data = api.get_collection_details(collection_id)

        if not details_data.get("success", False):
            messagebox.showerror("Ошибка", "Не удалось загрузить детали сборки")
            details_window.destroy()
            return

        collection = details_data["collection"]

        main_details_frame = ttk.Frame(details_window, padding=20)
        main_details_frame.pack(fill="both", expand=True)

        # Заголовок
        title_frame = ttk.Frame(main_details_frame)
        title_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(
            title_frame,
            text=collection["name"],
            font=("Comfortaa", 16, "bold")
        ).pack(side="left")

        # ID сборки
        ttk.Label(
            title_frame,
            text=f"ID: {collection_id[:8]}...",
            font=("Comfortaa", 8),
            foreground="gray"
        ).pack(side="right")

        # Метаданные
        meta_frame = ttk.Frame(main_details_frame)
        meta_frame.pack(fill="x", pady=(0, 15))

        # Первая строка метаданных
        meta_row1 = ttk.Frame(meta_frame)
        meta_row1.pack(fill="x", pady=2)

        ttk.Label(meta_row1, text=f"👤 Автор: {collection.get('uploader', 'Неизвестно')}",
                  font=("Comfortaa", 10)).pack(side="left", padx=(0, 15))
        ttk.Label(meta_row1, text=f"🎮 Minecraft: {collection.get('minecraft_version', '1.20.1')}",
                  font=("Comfortaa", 10)).pack(side="left", padx=(0, 15))

        # Вторая строка метаданных
        meta_row2 = ttk.Frame(meta_frame)
        meta_row2.pack(fill="x", pady=2)

        ttk.Label(meta_row2, text=f"⚙️ Загрузчик: {collection.get('loader', 'Fabric')}",
                  font=("Comfortaa", 10)).pack(side="left", padx=(0, 15))
        ttk.Label(meta_row2, text=f"📦 Модов: {collection.get('mod_count', 0)}",
                  font=("Comfortaa", 10)).pack(side="left", padx=(0, 15))
        ttk.Label(meta_row2, text=f"⬇️ Скачиваний: {collection.get('downloads', 0)}",
                  font=("Comfortaa", 10)).pack(side="left")

        if collection.get('description'):
            ttk.Label(main_details_frame, text="📝 Описание:",
                      font=("Comfortaa", 11, "bold")).pack(anchor="w", pady=(10, 5))
            desc_frame = ttk.Frame(main_details_frame)
            desc_frame.pack(fill="x", pady=(0, 15))

            desc_text = tk.Text(desc_frame, height=4, width=70, wrap="word", font=("Comfortaa", 9))
            desc_scrollbar = ttk.Scrollbar(desc_frame, orient="vertical", command=desc_text.yview)
            desc_text.configure(yscrollcommand=desc_scrollbar.set)

            desc_text.insert("1.0", collection['description'])
            desc_text.configure(state="disabled")

            desc_text.pack(side="left", fill="both", expand=True)
            desc_scrollbar.pack(side="right", fill="y")

        # Список модов
        ttk.Label(main_details_frame, text="📦 Моды в сборке:",
                  font=("Comfortaa", 11, "bold")).pack(anchor="w", pady=(10, 5))

        mods_frame = ttk.Frame(main_details_frame)
        mods_frame.pack(fill="both", expand=True, pady=(0, 15))

        mods_listbox = tk.Listbox(mods_frame, height=8, font=("Consolas", 9))
        mods_scrollbar = ttk.Scrollbar(mods_frame, orient="vertical", command=mods_listbox.yview)
        mods_listbox.configure(yscrollcommand=mods_scrollbar.set)

        mods_listbox.pack(side="left", fill="both", expand=True)
        mods_scrollbar.pack(side="right", fill="y")

        if "mods" in collection:
            for i, mod in enumerate(collection["mods"], 1):
                mod_name = mod.get("name", f"Мод {i}")
                source = mod.get("source", "unknown")

                # Добавляем иконку источника
                if source == "modrinth":
                    icon = "🌐"
                elif source == "curseforge":
                    icon = "⚡"
                elif source == "local":
                    icon = "💾"
                else:
                    icon = "❓"

                mods_listbox.insert("end", f"{i:2d}. {icon} {mod_name}")

        # Информация о совместимости
        compatibility_frame = ttk.Frame(main_details_frame)
        compatibility_frame.pack(fill="x", pady=(0, 10))

        loader = collection.get("loader", "").lower()
        if loader in ["fabric", "forge", "quilt", "neoforge"]:
            ttk.Label(compatibility_frame,
                      text=f"✅ Совместимость: {loader.capitalize()} {collection.get('loader_version', '')}",
                      foreground="green", font=("Comfortaa", 9)).pack(side="left")

        # Кнопки действий
        buttons_frame = ttk.Frame(main_details_frame)
        buttons_frame.pack(fill="x", pady=(15, 0))

        def download_and_import():
            """Скачать и импортировать сборку"""
            # Показываем прогресс
            progress_window = tk.Toplevel(details_window)
            progress_window.title("Скачивание сборки")
            progress_window.geometry("400x200")
            progress_window.transient(details_window)
            progress_window.grab_set()

            ttk.Label(progress_window, text=f"Скачиваем сборку '{collection['name']}'...",
                      font=("Comfortaa", 11)).pack(pady=15)

            status_label = ttk.Label(progress_window, text="Подготовка...")
            status_label.pack(pady=5)

            progress = ttk.Progressbar(progress_window, mode="indeterminate")
            progress.pack(pady=10)
            progress.start()

            def download_thread():
                status_label.config(text="Загрузка данных сборки...")

                # Скачиваем сборку
                result = api.download_collection(collection_id)

                if result.get("success", False):
                    status_label.config(text="Сохранение локально...")

                    try:
                        # Сохраняем в локальные сборки
                        collections_dir = COLLECTIONS_CONFIG["collections_dir"]
                        os.makedirs(collections_dir, exist_ok=True)

                        # Создаем безопасное имя файла
                        safe_name = "".join(
                            c for c in collection["name"] if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        safe_name = safe_name[:50]

                        # Проверяем, не существует ли уже такой сборки
                        filename = f"{safe_name}.json"
                        filepath = os.path.join(collections_dir, filename)

                        # Если файл существует, добавляем суффикс
                        counter = 1
                        while os.path.exists(filepath):
                            filename = f"{safe_name}_{counter}.json"
                            filepath = os.path.join(collections_dir, filename)
                            counter += 1

                        # Получаем данные сборки из результата
                        collection_data = result["collection"]

                        # Добавляем метаданные об источнике
                        collection_data["source"] = "community"
                        collection_data["original_id"] = collection_id
                        collection_data["imported_date"] = datetime.now().isoformat()
                        collection_data["imported_from"] = "community_server"

                        # Убедимся, что есть все необходимые поля
                        required_fields = ["name", "minecraft_version", "loader", "mods"]
                        for field in required_fields:
                            if field not in collection_data:
                                print(f"⚠️ Отсутствует поле {field} в данных сборки")

                        # Сохраняем файл
                        with open(filepath, "w", encoding="utf-8") as f:
                            json.dump(collection_data, f, indent=2, ensure_ascii=False)

                        valid, message = validate_collection_data(collection_data)
                        if not valid:
                            progress_window.destroy()
                            messagebox.showerror("Ошибка данных", f"Некорректные данные сборки:\n{message}")
                            return

                        # Проверяем, что файл сохранен
                        if os.path.exists(filepath):
                            print(f"✅ Файл сохранен: {filepath}")
                            file_size = os.path.getsize(filepath)
                            print(f"📏 Размер файла: {file_size} байт")

                            # Увеличиваем счетчик скачиваний на сервере
                            status_label.config(text="Обновление статистики...")
                            api.increment_downloads(collection_id)

                            progress_window.destroy()

                            messagebox.showinfo(
                                "✅ Успешно!",
                                f"Сборка '{collection['name']}' успешно импортирована!\n\n"
                                f"📁 Файл: {filename}\n"
                                f"📂 Папка: {collections_dir}\n"
                                f"📏 Размер: {file_size} байт\n\n"
                                f"Теперь сборка доступна в вашем локальном менеджере сборок."
                            )

                            details_window.destroy()

                            # Обновляем главное окно
                            if version_selector_callback:
                                version_selector_callback()

                        else:
                            progress_window.destroy()
                            messagebox.showerror(
                                "Ошибка сохранения",
                                "Не удалось сохранить файл сборки"
                            )

                    except Exception as e:
                        progress_window.destroy()
                        print(f"❌ Ошибка сохранения: {e}", exc_info=True)
                        messagebox.showerror(
                            "Ошибка сохранения",
                            f"Не удалось сохранить сборку:\n{str(e)}"
                        )
                else:
                    progress_window.destroy()
                    error_msg = result.get("error", "Неизвестная ошибка")
                    print(f"❌ Ошибка скачивания: {error_msg}")
                    messagebox.showerror(
                        "Ошибка скачивания",
                        f"Не удалось скачать сборку:\n{error_msg}"
                    )

            threading.Thread(target=download_thread, daemon=True).start()

        def validate_collection_data(data):
            """Проверка данных сборки на корректность"""
            required_fields = ["name", "minecraft_version", "loader"]

            # Проверяем обязательные поля
            for field in required_fields:
                if field not in data:
                    return False, f"Отсутствует обязательное поле: {field}"

            # Проверяем моды
            if "mods" not in data:
                data["mods"] = []
            elif not isinstance(data["mods"], list):
                return False, "Поле 'mods' должно быть списком"

            # Добавляем недостающие поля по умолчанию
            defaults = {
                "description": "",
                "category": "Другое",
                "visibility": "public",
                "loader_version": "",
                "mod_count": len(data.get("mods", []))
            }

            for field, default_value in defaults.items():
                if field not in data:
                    data[field] = default_value

            return True, "OK"


        def test_compatibility():
            """Проверить совместимость сборки"""
            from ConfDir.Versions import all_versions

            current_versions = [v for v in all_versions if not v.startswith("📦")]
            mc_version = collection.get("minecraft_version", "1.20.1")
            loader_type = collection.get("loader", "fabric")

            compatible_versions = []
            for version in current_versions:
                if mc_version in version and loader_type.lower() in version.lower():
                    compatible_versions.append(version)

            if compatible_versions:
                versions_text = "\n".join([f"• {v}" for v in compatible_versions[:5]])
                if len(compatible_versions) > 5:
                    versions_text += f"\n• ...и ещё {len(compatible_versions) - 5} версий"

                messagebox.showinfo(
                    "Совместимость сборки",
                    f"Эта сборка совместима со следующими версиями:\n\n{versions_text}\n\n"
                    f"Рекомендуемая версия: {mc_version} + {loader_type.capitalize()}"
                )
            else:
                messagebox.showinfo(
                    "Совместимость сборки",
                    f"Сборка создана для:\n"
                    f"• Minecraft {mc_version}\n"
                    f"• Загрузчик: {loader_type}\n\n"
                    f"Убедитесь, что у вас установлена нужная версия."
                )

        def copy_collection_id():
            """Копировать ID сборки"""
            details_window.clipboard_clear()
            details_window.clipboard_append(collection_id)
            details_window.update()
            messagebox.showinfo("Скопировано", f"ID сборки скопирован: {collection_id}")

        # Основные кнопки
        main_buttons_frame = ttk.Frame(buttons_frame)
        main_buttons_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(
            main_buttons_frame,
            text="⬇️ Скачать и импортировать",
            command=download_and_import,
            width=25
        ).pack(side="left", padx=5)

        ttk.Button(
            main_buttons_frame,
            text="🔍 Проверить совместимость",
            command=test_compatibility,
            width=20
        ).pack(side="left", padx=5)

        # Дополнительные кнопки
        extra_buttons_frame = ttk.Frame(buttons_frame)
        extra_buttons_frame.pack(fill="x")

        ttk.Button(
            extra_buttons_frame,
            text="📋 Копировать ID",
            command=copy_collection_id,
            width=15
        ).pack(side="left", padx=5)

        ttk.Button(
            extra_buttons_frame,
            text="❌ Закрыть",
            command=details_window.destroy,
            width=10
        ).pack(side="right", padx=5)

    # Привязка событий
    tree.bind("<Double-1>", on_collection_select)

    # Загрузка первой страницы
    load_collections_page(1)

    # Кнопка закрытия
    ttk.Button(main_frame, text="❌ Закрыть", command=community_window.destroy, width=20).pack(pady=(20, 0))


def upload_collection_dialog(parent_window):
    """Диалог загрузки сборки на сервер"""
    from ConfDir.Configs import COLLECTIONS_CONFIG

    upload_window = tk.Toplevel(parent_window)
    upload_window.title("📤 Загрузить сборку")
    upload_window.geometry("600x500")

    # Центрирование
    upload_window.update_idletasks()
    x = (parent_window.winfo_screenwidth() // 2) - (600 // 2)
    y = (parent_window.winfo_screenheight() // 2) - (500 // 2)
    upload_window.geometry(f"600x500+{x}+{y}")

    main_frame = ttk.Frame(upload_window, padding=20)
    main_frame.pack(fill="both", expand=True)

    ttk.Label(
        main_frame,
        text="📤 Загрузить сборку на сервер",
        font=("Comfortaa", 16, "bold")
    ).pack(pady=(0, 20))

    # Список локальных сборок
    collections_dir = COLLECTIONS_CONFIG["collections_dir"]

    if not os.path.exists(collections_dir):
        ttk.Label(main_frame, text="У вас нет локальных сборок", foreground="red").pack()
        ttk.Button(main_frame, text="Закрыть", command=upload_window.destroy).pack(pady=20)
        return

    local_collections = []
    for filename in os.listdir(collections_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(collections_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('name'):
                        local_collections.append((data['name'], filepath))
            except:
                continue

    if not local_collections:
        ttk.Label(main_frame, text="У вас нет локальных сборок", foreground="red").pack()
        ttk.Button(main_frame, text="Закрыть", command=upload_window.destroy).pack(pady=20)
        return

    # Выбор сборки
    ttk.Label(main_frame, text="Выберите сборку для загрузки:").pack(anchor="w", pady=(0, 5))

    collection_var = tk.StringVar()
    collection_combo = ttk.Combobox(
        main_frame,
        textvariable=collection_var,
        values=[name for name, _ in local_collections],
        state="readonly",
        width=50
    )
    collection_combo.pack(fill="x", pady=(0, 15))

    # Описание
    ttk.Label(main_frame, text="Описание (опционально):").pack(anchor="w", pady=(0, 5))
    description_text = tk.Text(main_frame, height=4, width=50)
    description_text.pack(fill="x", pady=(0, 15))

    # Категория
    ttk.Label(main_frame, text="Категория:").pack(anchor="w", pady=(0, 5))
    category_var = tk.StringVar(value="Другое")
    category_combo = ttk.Combobox(
        main_frame,
        textvariable=category_var,
        values=["Оптимизация", "Технологии", "Приключения", "Квесты", "Магия", "Биомы", "Строительство", "Выживание",
                "PvP", "Другое"],
        state="readonly",
        width=20
    )
    category_combo.pack(anchor="w", pady=(0, 15))

    # Видимость
    ttk.Label(main_frame, text="Видимость:").pack(anchor="w", pady=(0, 5))
    visibility_var = tk.StringVar(value="public")

    ttk.Radiobutton(
        main_frame,
        text="📢 Публичная (видна всем)",
        variable=visibility_var,
        value="public"
    ).pack(anchor="w")

    ttk.Radiobutton(
        main_frame,
        text="🔒 Приватная (только по ссылке)",
        variable=visibility_var,
        value="private"
    ).pack(anchor="w")

    def upload_selected():
        """Загрузить выбранную сборку"""
        selected_name = collection_var.get()
        if not selected_name:
            messagebox.showerror("Ошибка", "Выберите сборку")
            return

        # Находим путь к файлу
        filepath = None
        for name, path in local_collections:
            if name == selected_name:
                filepath = path
                break

        if not filepath or not os.path.exists(filepath):
            messagebox.showerror("Ошибка", "Файл сборки не найден")
            return

        # Загружаем данные сборки
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                collection_data = json.load(f)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочитать файл: {e}")
            return

        # Добавляем дополнительные данные
        collection_data["description"] = description_text.get("1.0", "end-1c").strip()
        collection_data["category"] = category_var.get()
        collection_data["visibility"] = visibility_var.get()

        # Создаем API экземпляр
        api = CommunityCollectionAPI()

        # Показываем прогресс
        progress_window = tk.Toplevel(upload_window)
        progress_window.title("Загрузка")
        progress_window.geometry("300x100")

        ttk.Label(progress_window, text="Загрузка сборки на сервер...").pack(pady=10)
        progress = ttk.Progressbar(progress_window, mode="indeterminate")
        progress.pack(pady=10)
        progress.start()

        def upload_thread():
            result = api.upload_collection(
                collection_data,
                username="anonymous"  # Здесь можно добавить имя пользователя
            )

            progress_window.destroy()

            if result.get("success", False):
                messagebox.showinfo(
                    "Успех",
                    f"Сборка '{selected_name}' успешно загружена на сервер!\n\n"
                    f"ID сборки: {result.get('collection_id', 'N/A')}\n"
                    f"Теперь её могут скачивать другие игроки."
                )
                upload_window.destroy()
            else:
                error_msg = result.get("error", "Неизвестная ошибка")
                messagebox.showerror("Ошибка", f"Не удалось загрузить сборку:\n{error_msg}")

        threading.Thread(target=upload_thread, daemon=True).start()

    # Кнопки
    buttons_frame = ttk.Frame(main_frame)
    buttons_frame.pack(fill="x", pady=(20, 0))

    ttk.Button(buttons_frame, text="📤 Загрузить", command=upload_selected).pack(side="left", padx=5)
    ttk.Button(buttons_frame, text="❌ Отмена", command=upload_window.destroy).pack(side="right", padx=5)