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

        self.versions = versions_list if versions_list else ["YamalPixel", "Minecraft 1.20.1 + Fabric"]

        # Создаем скрытый комбобокс
        self.combobox = ttk.Combobox(
            master, values=self.versions, state="readonly", font=("Comfortaa", 11)
        )
        self.combobox.current(0)
        self.combobox.configure(width=22, state="readonly")
        self.combobox.place_forget()

        # Текущее значение
        self.current_value = tk.StringVar(value=self.versions[0])

        # Бинды
        self.bind("<Button-1>", self.toggle_dropdown)
        self.combobox.bind("<<ComboboxSelected>>", self.on_select)

        # Начальная отрисовка
        self.draw_selector()

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

        # Текст выбранной версии
        display_text = self.current_value.get()
        if len(display_text) > 20:
            display_text = display_text[:20] + "..."

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
        icon_text = "🎮" if "YamalPixel" in self.current_value.get() else "⚙️"
        self.create_text(
            25,
            self.height // 2,
            text=icon_text,
            fill="white",
            font=("Comfortaa", 14),
            tags="icon",
        )

    def toggle_dropdown(self, event):
        """Открывает/закрывает выпадающий список"""
        if not self.is_open:
            self.combobox.place(
                x=self.winfo_x(),
                y=self.winfo_y() + self.height,
                width=self.width,
                height=200,
            )
            self.combobox.focus()
            self.combobox.event_generate("<Button-1>")
        else:
            self.hide_dropdown()

        self.is_open = not self.is_open
        self.draw_selector()

    def hide_dropdown(self):
        """Скрывает выпадающий список"""
        self.combobox.place_forget()

    def on_select(self, event):
        """Обрабатывает выбор версии"""
        selected = self.combobox.get()
        self.current_value.set(selected)
        self.is_open = False
        self.hide_dropdown()
        self.draw_selector()

    def hex_to_rgb(self, hex_color):
        """Конвертирует HEX в RGB"""
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(self, rgb):
        """Конвертирует RGB в HEX"""
        return "#{:02x}{:02x}{:02x}".format(*rgb)

    def get(self):
        """Возвращает выбранное значение"""
        return self.current_value.get()