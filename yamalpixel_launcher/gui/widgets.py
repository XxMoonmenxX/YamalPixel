# gui/widgets.py
import tkinter as tk
from tkinter import ttk

# Определение цветов (можно хранить в отдельном файле стилей)
WIDGET_COLORS = {
    "bg": "#1e1e1e",
    "fg": "#ffffff",
    "button_bg": "#2d2d2d",
    "button_hover": "#3e3e3e",
    "button_fg": "#ffffff",
    "entry_bg": "#2d2d2d",
    "entry_fg": "#ffffff",
    "border": "#444444",
    "online_bg": "#00aa00", # Зеленый для онлайн
    "offline_bg": "#aa0000", # Красный для оффлайн
}

class ModernButton(ttk.Button):
    """Кастомная кнопка с hover эффектом."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.default_bg = WIDGET_COLORS["button_bg"]
        self.hover_bg = WIDGET_COLORS["button_hover"]
        self.default_fg = WIDGET_COLORS["button_fg"]
        self.configure(
            style="Modern.TButton",
            cursor="hand2",
            takefocus=False, # Отключаем фокус для упрощения
        )
        # Привязываем события мыши
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self.configure(style="ModernHover.TButton")

    def on_leave(self, e):
        self.configure(style="Modern.TButton")

# Регистрация стилей для кнопки
style = ttk.Style()
style.configure("Modern.TButton", background=WIDGET_COLORS["button_bg"], foreground=WIDGET_COLORS["button_fg"])
style.map("Modern.TButton", background=[("!active", WIDGET_COLORS["button_bg"]), ("active", WIDGET_COLORS["button_hover"])])
style.configure("ModernHover.TButton", background=WIDGET_COLORS["button_hover"], foreground=WIDGET_COLORS["button_fg"])
style.map("ModernHover.TButton", background=[("!active", WIDGET_COLORS["button_hover"]), ("active", WIDGET_COLORS["button_bg"])])


class ModernOnlineButton(ttk.Button):
    """Кнопка, отображающая статус онлайн/оффлайн."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.online = False
        self.update_status(self.online)

    def update_status(self, is_online):
        self.online = is_online
        color = WIDGET_COLORS["online_bg"] if is_online else WIDGET_COLORS["offline_bg"]
        # ttk.Button не поддерживает изменение фона напрямую через configure
        # Для более сложного стиля можно использовать tk.Button с отрисовкой на Canvas
        # Пока просто обновим текст
        status_text = "🟢 Онлайн" if is_online else "🔴 Оффлайн"
        current_text = self.cget("text")
        # Предположим, что текст всегда в формате "Текст | Статус"
        base_text = current_text.split(" | ")[0] if " | " in current_text else current_text
        self.configure(text=f"{base_text} | {status_text}")
        # Примечание: Изменение цвета фона возможно через tk.Button или кастомный Canvas виджет


class ModernCombobox(ttk.Combobox):
    """Кастомная Combobox (может быть стилизована через ttk.Style)."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        # Стили Combobox обычно настраиваются через ttk.Style
        # Можно добавить логику, если нужно


class ModernCheckbutton(ttk.Checkbutton):
    """Кастомная Checkbutton (может быть стилизована через ttk.Style)."""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        # Стили Checkbutton обычно настраиваются через ttk.Style
        # Можно добавить логику, если нужно