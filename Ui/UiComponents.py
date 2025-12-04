import tkinter as tk
from tkinter import ttk
import math

class ModernButton(tk.Canvas):
    def __init__(
        self,
        master=None,
        text="Кнопка",
        width=200,
        height=50,
        gradient=("#FF6B6B", "#4ECDC4"),
        glow_color="#FF6B6B",
        animation="pulse",
        command=None,
        font_size=14,
        corner_radius=15,
        **kwargs,
    ):

        super().__init__(
            master, width=width, height=height, highlightthickness=0, **kwargs
        )

        self.text = text
        self.width = width
        self.height = height
        self.gradient = gradient
        self.glow_color = glow_color
        self.animation_type = animation
        self.command = command
        self.font_size = font_size
        self.corner_radius = corner_radius

        # Состояния кнопки
        self.is_pressed = False
        self.animation_running = True
        self.pulse_phase = 0

        # Цвета для разных состояний
        self.normal_gradient = gradient
        self.pressed_gradient = (
            self.darken_color(gradient[0]),
            self.darken_color(gradient[1]),
        )

        self.bind("<Button-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)

        # Начальная отрисовка
        self.draw_button()

        # Запускаем анимацию
        if animation == "pulse":
            self.animate_pulse()
        elif animation == "glow":
            self.animate_glow()

    def draw_button(self):
        """Отрисовывает кнопку"""
        self.delete("all")

        # Выбираем градиент в зависимости от состояния
        if self.is_pressed:
            grad_colors = self.pressed_gradient
        else:
            grad_colors = self.normal_gradient

        # Применяем пульсацию к цветам
        if self.animation_type == "pulse" and self.animation_running:
            pulse_factor = 0.1 * math.sin(self.pulse_phase)
            brightened_colors = (
                self.lighten_color(grad_colors[0], 0.1 + pulse_factor),
                self.lighten_color(grad_colors[1], 0.1 + pulse_factor),
            )
            grad_colors = brightened_colors

        # Простой прямоугольник со скругленными углами (без сложной геометрии)
        self.create_rectangle(
            2,
            2,
            self.width - 2,
            self.height - 2,
            fill=grad_colors[0],
            outline="",
            width=0,
            tags="bg",
        )

        # Упрощенный градиент
        steps = 10
        for i in range(steps):
            ratio = i / steps
            r = int(
                (1 - ratio) * self.hex_to_rgb(grad_colors[0])[0]
                + ratio * self.hex_to_rgb(grad_colors[1])[0]
            )
            g = int(
                (1 - ratio) * self.hex_to_rgb(grad_colors[0])[1]
                + ratio * self.hex_to_rgb(grad_colors[1])[1]
            )
            b = int(
                (1 - ratio) * self.hex_to_rgb(grad_colors[0])[2]
                + ratio * self.hex_to_rgb(grad_colors[1])[2]
            )

            color = self.rgb_to_hex((r, g, b))
            x1 = i * (self.width / steps)
            x2 = (i + 1) * (self.width / steps)
            self.create_rectangle(
                x1, 2, x2, self.height - 2, fill=color, outline="", tags="gradient"
            )

        # Добавляем текст
        text_color = "white"
        self.create_text(
            self.width / 2,
            self.height / 2,
            text=self.text,
            fill=text_color,
            font=("Comfortaa", self.font_size, "bold"),
            tags="text",
        )

        # Добавляем свечение
        if self.animation_type == "pulse" and self.animation_running:
            glow_intensity = abs(math.sin(self.pulse_phase)) * 0.3
            glow_width = 2 + int(glow_intensity * 4)
            self.create_rectangle(
                0,
                0,
                self.width,
                self.height,
                outline=self.glow_color,
                width=glow_width,
                tags="glow",
            )

    def animate_pulse(self):
        """Анимация пульсации"""
        if not self.animation_running:
            return

        self.pulse_phase += 0.1
        if self.pulse_phase > 2 * math.pi:
            self.pulse_phase = 0

        self.draw_button()
        self.after(50, self.animate_pulse)

    def animate_glow(self):
        """Анимация свечения"""
        if not self.animation_running:
            return

        self.pulse_phase += 0.15
        self.draw_button()
        self.after(80, self.animate_glow)

    def on_hover(self, event):
        """При наведении курсора"""
        self.draw_button()

    def on_leave(self, event):
        """При уходе курсора"""
        self.draw_button()

    def on_press(self, event):
        """При нажатии"""
        self.is_pressed = True
        self.pulse_phase += 0.5
        self.draw_button()

    def on_release(self, event):
        """При отпускании"""
        self.is_pressed = False
        self.draw_button()

        if self.command:
            self.command()

    def lighten_color(self, color, factor=0.2):
        """Осветляет цвет"""
        rgb = self.hex_to_rgb(color)
        rgb = [min(255, c + int(255 * factor)) for c in rgb]
        return self.rgb_to_hex(rgb)

    def darken_color(self, color, factor=0.2):
        """Затемняет цвет"""
        rgb = self.hex_to_rgb(color)
        rgb = [max(0, c - int(255 * factor)) for c in rgb]
        return self.rgb_to_hex(rgb)

    def hex_to_rgb(self, hex_color):
        """Конвертирует HEX в RGB"""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb):
        """Конвертирует RGB в HEX"""
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    def stop_animation(self):
        """Останавливает анимацию"""
        self.animation_running = False

    def start_animation(self):
        """Запускает анимацию"""
        self.animation_running = True
        if self.animation_type == "pulse":
            self.animate_pulse()
        elif self.animation_type == "glow":
            self.animate_glow()


class ModernCheckbutton(tk.Canvas):
    def __init__(
        self,
        master=None,
        text="",
        variable=None,
        command=None,
        width=180,
        height=28,
        **kwargs,
    ):

        super().__init__(
            master, width=width, height=height, highlightthickness=0, **kwargs
        )

        self.configure(bg="#2b2b2b")
        self.text = text
        self.variable = variable
        self.command = command
        self._width = width  # Сохраняем как атрибуты
        self._height = height

        self.bind("<Button-1>", self.toggle)
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)

        self.is_hovered = False
        self.draw_checkbutton()

    def draw_checkbutton(self):
        self.delete("all")

        checkbox_size = 18
        checkbox_x, checkbox_y = 8, (self._height - checkbox_size) // 2

        # Чекбокс с градиентом если выбран
        if self.variable.get():
            # Красивый градиентный эффект для выбранного состояния
            self.create_rectangle(
                checkbox_x,
                checkbox_y,
                checkbox_x + checkbox_size,
                checkbox_y + checkbox_size,
                fill="#667eea",
                outline="#4ECDC4",
                width=2,
            )
            self.create_text(
                checkbox_x + checkbox_size // 2,
                checkbox_y + checkbox_size // 2,
                text="✓",
                fill="white",
                font=("Arial", 10, "bold"),
            )
        else:
            # Стильный для невыбранного
            bg_color = "#555" if self.is_hovered else "#444"
            self.create_rectangle(
                checkbox_x,
                checkbox_y,
                checkbox_x + checkbox_size,
                checkbox_y + checkbox_size,
                fill=bg_color,
                outline="#666",
                width=1,
            )

        # Красивый текст с эмодзи
        text_color = "#ffffff" if self.is_hovered else "#e0e0e0"
        self.create_text(
            checkbox_x + checkbox_size + 12,
            self._height // 2,
            text=self.text,
            fill=text_color,
            anchor="w",
            font=("Comfortaa", 11),
        )

        # Добавляем легкую анимацию при наведении
        if self.is_hovered:
            self.create_rectangle(
                0, 0, self._width, self._height, outline="#667eea", width=1
            )

    def toggle(self, event):
        self.variable.set(not self.variable.get())
        self.draw_checkbutton()
        if self.command:
            self.command()

    def on_hover(self, event):
        self.is_hovered = True
        self.draw_checkbutton()

    def on_leave(self, event):
        self.is_hovered = False
        self.draw_checkbutton()


class ModernCloseButton(tk.Canvas):
    def __init__(
        self,
        master=None,
        text="❌ ЗАКРЫТЬ",
        width=120,
        height=35,
        gradient=("#ff6b6b", "#ff4757"),
        glow_color="#ff4757",
        command=None,
        font_size=11,
        corner_radius=10,
        **kwargs,
    ):

        super().__init__(
            master, width=width, height=height, highlightthickness=0, **kwargs
        )

        self.configure(bg="#2b2b2b")

        self.text = text
        self.width = width
        self.height = height
        self.gradient = gradient
        self.glow_color = glow_color
        self.command = command
        self.font_size = font_size
        self.corner_radius = corner_radius

        # Состояния кнопки
        self.is_pressed = False
        self.animation_running = True
        self.pulse_phase = 0

        self.bind("<Button-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)

        # Начальная отрисовка
        self.draw_button()
        self.animate_glow()

    def draw_button(self):
        """Отрисовывает кнопку закрытия"""
        self.delete("all")

        # Выбираем градиент в зависимости от состояния
        if self.is_pressed:
            grad_colors = (
                self.darken_color(self.gradient[0]),
                self.darken_color(self.gradient[1]),
            )
        else:
            grad_colors = self.gradient

        # Добавляем эффект пульсации при наведении
        if self.animation_running:
            glow_intensity = abs(math.sin(self.pulse_phase)) * 0.3
            brightened_colors = (
                self.lighten_color(grad_colors[0], glow_intensity),
                self.lighten_color(grad_colors[1], glow_intensity),
            )
            grad_colors = brightened_colors

        # Градиентный фон
        steps = 8
        for i in range(steps):
            ratio = i / steps
            r = int(
                (1 - ratio) * self.hex_to_rgb(grad_colors[0])[0]
                + ratio * self.hex_to_rgb(grad_colors[1])[0]
            )
            g = int(
                (1 - ratio) * self.hex_to_rgb(grad_colors[0])[1]
                + ratio * self.hex_to_rgb(grad_colors[1])[1]
            )
            b = int(
                (1 - ratio) * self.hex_to_rgb(grad_colors[0])[2]
                + ratio * self.hex_to_rgb(grad_colors[1])[2]
            )

            color = self.rgb_to_hex((r, g, b))
            x1 = i * (self.width / steps)
            x2 = (i + 1) * (self.width / steps)

            self.create_rectangle(
                x1, 2, x2, self.height - 2, fill=color, outline="", tags="gradient"
            )

        # Обводка
        border_color = "#ffffff" if self.is_pressed else self.glow_color
        self.create_rectangle(
            1,
            1,
            self.width - 1,
            self.height - 1,
            outline=border_color,
            width=2,
            tags="border",
        )

        # Текст
        text_color = "white"
        self.create_text(
            self.width / 2,
            self.height / 2,
            text=self.text,
            fill=text_color,
            font=("Comfortaa", self.font_size, "bold"),
            tags="text",
        )

        # Свечение
        if self.animation_running:
            glow_width = 1 + int(abs(math.sin(self.pulse_phase)) * 2)
            self.create_rectangle(
                0,
                0,
                self.width,
                self.height,
                outline=self.glow_color,
                width=glow_width,
                tags="glow",
            )

    def animate_glow(self):
        """Анимация свечения"""
        if not self.animation_running:
            return

        self.pulse_phase += 0.1
        if self.pulse_phase > 2 * math.pi:
            self.pulse_phase = 0

        self.draw_button()
        self.after(80, self.animate_glow)

    def on_hover(self, event):
        """При наведении курсора"""
        self.animation_running = True
        self.draw_button()

    def on_leave(self, event):
        """При уходе курсора"""
        self.animation_running = False
        self.draw_button()

    def on_press(self, event):
        """При нажатии"""
        self.is_pressed = True
        self.draw_button()

    def on_release(self, event):
        """При отпускании"""
        self.is_pressed = False
        self.draw_button()

        if self.command:
            import tkinter.messagebox as messagebox
            # Подтверждение закрытия
            if messagebox.askyesno(
                "Закрыть лаунчер",
                "Точно хотите выйти?\n\nВсе настройки будут сохранены.",
            ):
                self.command()

    def lighten_color(self, color, factor=0.2):
        """Осветляет цвет"""
        rgb = self.hex_to_rgb(color)
        rgb = [min(255, c + int(255 * factor)) for c in rgb]
        return self.rgb_to_hex(rgb)

    def darken_color(self, color, factor=0.2):
        """Затемняет цвет"""
        rgb = self.hex_to_rgb(color)
        rgb = [max(0, c - int(255 * factor)) for c in rgb]
        return self.rgb_to_hex(rgb)

    def hex_to_rgb(self, hex_color):
        """Конвертирует HEX в RGB"""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb):
        """Конвертирует RGB в HEX"""
        return "#{:02x}{:02x}{:02x}".format(*rgb)


class ModernEntry(tk.Canvas):
    def __init__(
        self,
        master=None,
        placeholder="Введите никнейм",
        width=280,
        height=48,
        gradient=("#667eea", "#764ba2"),
        corner_radius=15,
        **kwargs,
    ):

        super().__init__(
            master, width=width, height=height, highlightthickness=0, **kwargs
        )

        self.configure(bg="#2b2b2b")

        self.placeholder = placeholder
        self.width = width
        self.height = height
        self.gradient = gradient
        self.corner_radius = corner_radius
        self.is_focused = False
        self.text_value = tk.StringVar()

        # ВАЖНО: сначала рисуем градиент, потом создаем Entry поверх
        self.draw_background()

        # Создаем Entry ПОВЕРХ градиента
        self.entry = tk.Entry(
            self,
            textvariable=self.text_value,
            font=("Comfortaa", 12),
            border=0,
            relief="flat",
            bg="white",
            fg="#2b2b2b",
            justify="center",
            insertbackground="#2b2b2b",
            highlightthickness=0,
        )

        # Размещаем Entry поверх всего
        self.entry.place(x=10, y=10, width=width - 20, height=height - 20)

        # Бинды
        self.entry.bind("<FocusIn>", self.on_focus_in)
        self.entry.bind("<FocusOut>", self.on_focus_out)
        self.entry.bind("<KeyRelease>", self.on_key_release)

        self.update_placeholder()

    def draw_background(self):
        """Отрисовывает градиентный фон"""
        self.delete("all")

        # Градиентный фон
        steps = 12
        for i in range(steps):
            ratio = i / steps
            r = int(
                (1 - ratio) * self.hex_to_rgb(self.gradient[0])[0]
                + ratio * self.hex_to_rgb(self.gradient[1])[0]
            )
            g = int(
                (1 - ratio) * self.hex_to_rgb(self.gradient[0])[1]
                + ratio * self.hex_to_rgb(self.gradient[1])[1]
            )
            b = int(
                (1 - ratio) * self.hex_to_rgb(self.gradient[0])[2]
                + ratio * self.hex_to_rgb(self.gradient[1])[2]
            )

            color = self.rgb_to_hex((r, g, b))
            x1 = i * (self.width / steps)
            x2 = (i + 1) * (self.width / steps)

            self.create_rectangle(
                x1, 0, x2, self.height, fill=color, outline="", tags="gradient"
            )

        # Обводка
        border_color = "#ffffff" if self.is_focused else self.gradient[1]
        border_width = 3 if self.is_focused else 2
        self.create_rectangle(
            2,
            2,
            self.width - 2,
            self.height - 2,
            outline=border_color,
            width=border_width,
            tags="border",
        )

    def on_focus_in(self, event):
        """При фокусе"""
        self.is_focused = True
        self.draw_background()
        if self.text_value.get() == self.placeholder:
            self.entry.configure(fg="#2b2b2b")
            self.text_value.set("")

    def on_focus_out(self, event):
        """При потере фокуса"""
        self.is_focused = False
        self.draw_background()
        self.update_placeholder()

    def on_key_release(self, event):
        """При вводе текста"""
        pass  # Не нужно перерисовывать

    def update_placeholder(self):
        """Обновляет плейсхолдер"""
        if not self.text_value.get() and not self.is_focused:
            self.entry.configure(fg="#666666")
            self.text_value.set(self.placeholder)
        else:
            self.entry.configure(fg="#2b2b2b")

    def get(self):
        """Возвращает текст (без плейсхолдера)"""
        text = self.text_value.get()
        return "" if text == self.placeholder else text

    def hex_to_rgb(self, hex_color):
        """Конвертирует HEX в RGB"""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb):
        """Конвертирует RGB в HEX"""
        return "#{:02x}{:02x}{:02x}".format(*rgb)


class ModernOnlineButton(ModernButton):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('gradient', ("#4A90E2", "#357ABD"))
        kwargs.setdefault('glow_color', "#4A90E2")
        kwargs.setdefault('animation', "glow")
        super().__init__(*args, **kwargs)


import tkinter as tk
from tkinter import ttk
import json
import os


class ModernVersionSelector(tk.Canvas):
    def __init__(
            self,
            master=None,
            width=300,
            height=50,
            gradient=("#667eea", "#764ba2"),
            corner_radius=15,
            versions_list=None,
            **kwargs,
    ):
        super().__init__(
            master, width=width, height=height, highlightthickness=0, **kwargs
        )

        self.configure(bg="#2b2b2b")

        self.width = width
        self.height = height
        self.gradient = gradient
        self.corner_radius = corner_radius
        self.is_open = False
        self.master = master

        # Инициализируем список версий
        self.all_versions = []

        # Загружаем версии из файла Versions.py
        self.load_all_versions()

        # Создаем кастомный выпадающий список
        self.dropdown_window = None
        self.dropdown_frame = None
        self.inner_frame = None
        self.canvas = None
        self.scrollbar = None
        self.item_height = 35
        self.max_visible_items = 8
        self.dropdown_height = self.item_height * self.max_visible_items

        # Текущее значение
        if self.all_versions:
            self.current_value = tk.StringVar(value=self.all_versions[0])
        else:
            self.current_value = tk.StringVar(value="YamalPixel")

        # Бинды
        self.bind("<Button-1>", self.toggle_dropdown)

        # Начальная отрисовка
        self.draw_selector()

    def load_all_versions(self):
        """Загружает все версии: статические и пользовательские сборки"""
        try:
            # Используем функцию get_all_versions() из Versions.py
            from ConfDir.Versions import get_all_versions
            self.all_versions = get_all_versions()
            print(f"✅ Загружено {len(self.all_versions)} версий через get_all_versions()")

        except ImportError as e:
            print(f"❌ Ошибка импорта Versions.py: {e}")
            # Запасной вариант
            self.all_versions = ["YamalPixel", "Minecraft 1.20.1 + Fabric"]
            print(f"📋 Используем дефолтные версии: {len(self.all_versions)}")

        except Exception as e:
            print(f"❌ Ошибка при загрузке всех версий: {e}")
            import traceback
            traceback.print_exc()
            self.all_versions = ["YamalPixel", "Minecraft 1.20.1 + Fabric"]

    def get_collection_info(self, collection_name):
        """Получает информацию о кастомной сборке из JSON файла"""
        try:
            # Убираем эмодзи из названия
            clean_name = collection_name
            if collection_name.startswith("📦 "):
                clean_name = collection_name[2:]  # Убираем "📦 "

            print(f"🔍 Поиск сборки: {clean_name}")

            # Ищем сборку в папке коллекций
            try:
                from ConfDir.Configs import COLLECTIONS_CONFIG
                collections_dir = COLLECTIONS_CONFIG["collections_dir"]
            except ImportError:
                collections_dir = "collections"

            if not os.path.exists(collections_dir):
                print(f"❌ Папка сборок не существует: {collections_dir}")
                return None, None, None

            for filename in os.listdir(collections_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(collections_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        if data.get('name') == clean_name:
                            print(f"✅ Найден файл сборки: {filename}")
                            return (
                                data.get('minecraft_version'),
                                data.get('loader', 'fabric'),
                                filepath
                            )
                    except Exception as e:
                        print(f"⚠️ Ошибка чтения файла {filename}: {e}")

            print(f"❌ Сборка '{clean_name}' не найдена")
            return None, None, None

        except Exception as e:
            print(f"❌ Ошибка при получении информации о сборке: {e}")
            import traceback
            traceback.print_exc()
            return None, None, None

    def on_version_selected(self, version):
        """Обработчик выбора версии"""
        try:
            # Проверяем, является ли это кастомной сборкой
            if version.startswith("📦"):
                # Получаем информацию о сборке из JSON
                minecraft_version, loader, collection_path = self.get_collection_info(version)

                if minecraft_version:
                    print(f"🎮 Выбрана кастомная сборка: {version[2:]}")
                    print(f"🟩 Версия Minecraft: {minecraft_version}")
                    print(f"🛠️ Загрузчик: {loader if loader else 'Не указан'}")
                    print(f"📁 Путь к сборке: {collection_path}")

                    # Генерируем событие с дополнительными данными
                    self.event_generate("<<CustomCollectionSelected>>",
                                        data={
                                            'name': version[2:],  # Без эмодзи
                                            'display_name': version,
                                            'minecraft_version': minecraft_version,
                                            'loader': loader,
                                            'path': collection_path
                                        })
                else:
                    print(f"⚠️ Не удалось получить информацию о сборке: {version}")
            else:
                # Статическая версия
                print(f"🎮 Выбрана версия: {version}")

                # Импортируем необходимые функции
                try:
                    from ConfDir.Versions import get_version_config, get_minecraft_version, is_modloader_needed

                    # Получаем конфигурацию версии
                    config = get_version_config(version)
                    if config:
                        print(f"📋 Конфигурация: Minecraft {config[0]}, Loader: {config[1]}")

                    # Получаем версию Minecraft
                    mc_version = get_minecraft_version(version)
                    print(f"🟩 Версия Minecraft: {mc_version}")

                    # Проверяем нужен ли модлоадер
                    loader = is_modloader_needed(version)
                    if loader:
                        print(f"🛠️ Требуется модлоадер: {loader}")
                    else:
                        print("🎮 Ванильная версия (модлоадер не требуется)")

                except ImportError as e:
                    print(f"⚠️ Не удалось импортировать функции из Versions.py: {e}")

            # Генерируем стандартное событие
            self.event_generate("<<VersionSelected>>", data=version)

        except Exception as e:
            print(f"❌ Ошибка при обработке выбора версии: {e}")
            import traceback
            traceback.print_exc()

    def get_selected_version_info(self):
        """Возвращает информацию о выбранной версии"""
        selected = self.get()

        if selected.startswith("📦"):
            # Кастомная сборка
            minecraft_version, loader, path = self.get_collection_info(selected)
            return {
                'type': 'custom',
                'display_name': selected,
                'name': selected[2:],  # Без эмодзи
                'minecraft_version': minecraft_version,
                'loader': loader,
                'path': path
            }
        else:
            # Статическая версия
            try:
                from ConfDir.Versions import get_minecraft_version, is_modloader_needed

                return {
                    'type': 'static',
                    'display_name': selected,
                    'name': selected,
                    'minecraft_version': get_minecraft_version(selected),
                    'loader': is_modloader_needed(selected)
                }
            except ImportError:
                # Запасной вариант если не удалось импортировать
                if "1.20.1" in selected:
                    mc_version = "1.20.1"
                elif "1.21" in selected:
                    mc_version = "1.21.1"
                else:
                    mc_version = "1.20.1"  # Дефолт

                loader = None
                if "Fabric" in selected:
                    loader = "fabric"
                elif "Forge" in selected:
                    loader = "forge"
                elif "NeoForge" in selected:
                    loader = "neoforge"
                elif "Quilt" in selected:
                    loader = "quilt"

                return {
                    'type': 'static',
                    'display_name': selected,
                    'name': selected,
                    'minecraft_version': mc_version,
                    'loader': loader
                }

    def draw_selector(self):
        """Отрисовывает селектор версий"""
        self.delete("all")

        # Градиентный фон
        steps = 12
        for i in range(steps):
            ratio = i / steps
            r = int(
                (1 - ratio) * self.hex_to_rgb(self.gradient[0])[0]
                + ratio * self.hex_to_rgb(self.gradient[1])[0]
            )
            g = int(
                (1 - ratio) * self.hex_to_rgb(self.gradient[0])[1]
                + ratio * self.hex_to_rgb(self.gradient[1])[1]
            )
            b = int(
                (1 - ratio) * self.hex_to_rgb(self.gradient[0])[2]
                + ratio * self.hex_to_rgb(self.gradient[1])[2]
            )

            color = self.rgb_to_hex((r, g, b))
            x1 = i * (self.width / steps)
            x2 = (i + 1) * (self.width / steps)

            self.create_rectangle(
                x1, 2, x2, self.height - 2, fill=color, outline="", tags="gradient"
            )

        # Текст выбранной версии (сокращаем если нужно)
        display_text = self.current_value.get()
        if len(display_text) > 25:
            display_text = display_text[:22] + "..."

        self.create_text(
            self.width // 2 - 10,
            self.height // 2,
            text=display_text,
            fill="white",
            font=("Comfortaa", 11),
            anchor="e",
            tags="text",
        )

        # Стрелка
        arrow_size = 6
        center_x = self.width - 20
        center_y = self.height // 2

        if self.is_open:
            # Стрелка вверх
            points = [
                center_x,
                center_y - arrow_size // 2,
                center_x - arrow_size,
                center_y + arrow_size // 2,
                center_x + arrow_size,
                center_y + arrow_size // 2,
            ]
        else:
            # Стрелка вниз
            points = [
                center_x,
                center_y + arrow_size // 2,
                center_x - arrow_size,
                center_y - arrow_size // 2,
                center_x + arrow_size,
                center_y - arrow_size // 2,
            ]

        self.create_polygon(points, fill="white", tags="arrow")

        # Иконка версии
        current_val = self.current_value.get()
        if current_val.startswith("📦"):
            icon_text = "📦"  # Пользовательская сборка
        elif "Fabric" in current_val:
            icon_text = "🧵"
        elif "Forge" in current_val:
            icon_text = "🔨"
        elif "Quilt" in current_val:
            icon_text = "🛋️"
        elif "NeoForge" in current_val:
            icon_text = "⚡"
        else:
            icon_text = "🎮"  # Ванильная версия

        self.create_text(
            25,
            self.height // 2,
            text=icon_text,
            fill="white",
            font=("Comfortaa", 14),
            tags="icon",
        )

    def toggle_dropdown(self, event):
        """Открывает/закрывает выпадающий список с прокруткой"""
        if not self.is_open:
            self.show_dropdown()
        else:
            self.hide_dropdown()

        self.is_open = not self.is_open
        self.draw_selector()

    def show_dropdown(self):
        """Показывает кастомный выпадающий список с прокруткой"""
        # Обновляем список версий перед показом
        self.refresh_versions()

        # Создаем окно для выпадающего списка
        self.dropdown_window = tk.Toplevel(self.master)
        self.dropdown_window.overrideredirect(True)
        self.dropdown_window.configure(bg="#3a3a3a", relief="solid", borderwidth=1)

        # Позиционируем под селектором
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.height

        # Высота окна зависит от количества элементов
        item_count = len(self.all_versions)
        window_height = min(item_count * self.item_height, self.dropdown_height) + 2

        self.dropdown_window.geometry(f"{self.width}x{window_height}+{x}+{y}")

        # Создаем Canvas для скроллинга
        self.canvas = tk.Canvas(
            self.dropdown_window,
            bg="#3a3a3a",
            highlightthickness=0,
            width=self.width - 15,
            height=window_height - 2
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        # Создаем фрейм для элементов ВНУТРИ canvas
        self.inner_frame = tk.Frame(self.canvas, bg="#3a3a3a")
        self.canvas_frame = self.canvas.create_window((0, 0), window=self.inner_frame,
                                                      anchor="nw", width=self.width - 15)

        # Добавляем элементы версий
        self.create_dropdown_items()

        # Обновляем размер внутреннего фрейма
        self.inner_frame.update_idletasks()

        # Настраиваем скроллинг
        canvas_height = window_height - 2
        frame_height = self.inner_frame.winfo_reqheight()

        # Если контент больше высоты canvas, добавляем скроллбар
        if frame_height > canvas_height:
            self.scrollbar = tk.Scrollbar(
                self.dropdown_window,
                orient="vertical",
                command=self.canvas.yview
            )
            self.scrollbar.pack(side="right", fill="y")

            self.canvas.configure(yscrollcommand=self.scrollbar.set)
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            # Привязываем колесико мыши
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Привязываем события
        self.dropdown_window.bind("<FocusOut>", self.on_dropdown_focus_out)
        self.dropdown_window.bind("<Escape>", self.hide_dropdown)
        self.master.bind("<Button-1>", self.on_master_click)

        # Устанавливаем фокус
        self.dropdown_window.focus_set()

        # Прокручиваем к выбранному элементу
        self.scroll_to_selected()

    def _on_mousewheel(self, event):
        """Обработка колесика мыши для скроллинга"""
        if self.canvas and self.scrollbar:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_dropdown_items(self):
        """Создает элементы в выпадающем списке"""
        for idx, version in enumerate(self.all_versions):
            item_frame = tk.Frame(
                self.inner_frame,
                bg="#3a3a3a",
                height=self.item_height,
                width=self.width - 15,
                cursor="hand2"
            )
            item_frame.pack(fill="x", pady=0)
            item_frame.pack_propagate(False)

            # Иконка
            icon_frame = tk.Frame(item_frame, bg="#3a3a3a")
            icon_frame.pack(side="left", padx=(10, 5))

            if version.startswith("📦"):
                icon_text = "📦"
                icon_color = "#FF6B9D"
            elif "Fabric" in version:
                icon_text = "🧵"
                icon_color = "#00A0FF"
            elif "Forge" in version:
                icon_text = "🔨"
                icon_color = "#F0A500"
            elif "Quilt" in version:
                icon_text = "🛋️"
                icon_color = "#AA00FF"
            elif "NeoForge" in version:
                icon_text = "⚡"
                icon_color = "#00FFAA"
            else:
                icon_text = "🎮"
                icon_color = "#4CAF50"

            icon_label = tk.Label(
                icon_frame,
                text=icon_text,
                bg="#3a3a3a",
                fg=icon_color,
                font=("Comfortaa", 12)
            )
            icon_label.pack()

            # Текст
            text_label = tk.Label(
                item_frame,
                text=version,
                bg="#3a3a3a",
                fg="white",
                font=("Comfortaa", 11),
                anchor="w",
                padx=5,
                cursor="hand2"
            )
            text_label.pack(side="left", fill="both", expand=True)

            # Выделение выбранного элемента
            if version == self.current_value.get():
                item_frame.configure(bg="#4a4a4a")
                icon_frame.configure(bg="#4a4a4a")
                icon_label.configure(bg="#4a4a4a")
                text_label.configure(bg="#4a4a4a")

            # События
            def make_lambda(v=version, f=item_frame, i=icon_frame, il=icon_label, tl=text_label):
                return lambda e: self.on_item_click(v, f, i, il, tl)

            item_frame.bind("<Enter>", lambda e, f=item_frame, i=icon_frame, il=icon_label, tl=text_label:
            self.on_item_hover(f, i, il, tl, True))
            item_frame.bind("<Leave>", lambda e, f=item_frame, i=icon_frame, il=icon_label, tl=text_label:
            self.on_item_hover(f, i, il, tl, False))
            item_frame.bind("<Button-1>", make_lambda())

            text_label.bind("<Enter>", lambda e, f=item_frame, i=icon_frame, il=icon_label, tl=text_label:
            self.on_item_hover(f, i, il, tl, True))
            text_label.bind("<Leave>", lambda e, f=item_frame, i=icon_frame, il=icon_label, tl=text_label:
            self.on_item_hover(f, i, il, tl, False))
            text_label.bind("<Button-1>", make_lambda())

            icon_label.bind("<Button-1>", make_lambda())

    def scroll_to_selected(self):
        """Прокручивает список к выбранному элементу"""
        if not self.canvas or not self.inner_frame:
            return

        try:
            selected_index = self.all_versions.index(self.current_value.get())
            y_position = selected_index * self.item_height
            visible_height = self.dropdown_height
            total_height = len(self.all_versions) * self.item_height

            if y_position + self.item_height > visible_height:
                scroll_position = (y_position - visible_height + self.item_height) / total_height
                self.canvas.yview_moveto(scroll_position)
        except (ValueError, IndexError):
            pass

    def on_item_hover(self, frame, icon_frame, icon_label, text_label, is_hover):
        """Обработка наведения на элемент"""
        if is_hover:
            frame.configure(bg="#4a4a4a")
            icon_frame.configure(bg="#4a4a4a")
            icon_label.configure(bg="#4a4a4a")
            text_label.configure(bg="#4a4a4a")
        else:
            if text_label.cget("text") != self.current_value.get():
                frame.configure(bg="#3a3a3a")
                icon_frame.configure(bg="#3a3a3a")
                icon_label.configure(bg="#3a3a3a")
                text_label.configure(bg="#3a3a3a")

    def on_item_click(self, version, frame, icon_frame, icon_label, text_label):
        """Обработка клика по элементу"""
        self.current_value.set(version)
        self.hide_dropdown()
        self.is_open = False
        self.draw_selector()
        self.on_version_selected(version)

    def on_dropdown_focus_out(self, event):
        """Закрывает список при потере фокуса"""
        self.after(150, self.check_focus)

    def check_focus(self):
        """Проверяет фокус и закрывает список если нужно"""
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            try:
                if not self.dropdown_window.focus_displayof():
                    self.hide_dropdown()
            except:
                self.hide_dropdown()

    def on_master_click(self, event):
        """Обработка клика вне выпадающего списка"""
        if self.is_open and self.dropdown_window:
            widget = event.widget
            while widget:
                if widget == self.dropdown_window:
                    return
                widget = widget.master

            self.hide_dropdown()

    def hide_dropdown(self, event=None):
        """Скрывает выпадающий список"""
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            if self.canvas:
                try:
                    self.canvas.unbind_all("<MouseWheel>")
                except:
                    pass

            self.dropdown_window.destroy()
            self.dropdown_window = None
            self.inner_frame = None
            self.canvas = None
            self.scrollbar = None

            try:
                self.master.unbind("<Button-1>")
            except:
                pass

            self.is_open = False
            self.draw_selector()

    def hex_to_rgb(self, hex_color):
        """Конвертирует HEX в RGB"""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i: i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb):
        """Конвертирует RGB в HEX"""
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    def get(self):
        """Возвращает выбранное значение"""
        return self.current_value.get()

    def set(self, version):
        """Устанавливает выбранную версию"""
        if version in self.all_versions:
            self.current_value.set(version)
            self.draw_selector()
        else:
            print(f"⚠️ Версия '{version}' не найдена в списке")

    def refresh_versions(self):
        """Обновляет список версий"""


        # Сохраняем текущее выбранное значение
        current_selection = self.current_value.get()

        # Сохраняем старый список
        old_versions = self.all_versions.copy()

        # Загружаем новые версии
        try:
            from ConfDir.Versions import get_all_versions
            self.all_versions = get_all_versions()
        except:
            # Запасной вариант
            self.all_versions = old_versions


        # Проверяем, осталось ли текущее выбранное значение в списке
        if current_selection not in self.all_versions and self.all_versions:
            # Если текущего значения больше нет, выбираем первое в списке
            self.current_value.set(self.all_versions[0])
        elif current_selection in self.all_versions:
            # Если значение осталось, восстанавливаем его
            self.current_value.set(current_selection)
        else:
            print(f"❌ Нет доступных версий!")

        # Перерисовываем селектор
        self.draw_selector()


        return old_versions != self.all_versions

    def destroy(self):
        """Корректное уничтожение виджета"""
        try:
            self.hide_dropdown()
        finally:
            super().destroy()