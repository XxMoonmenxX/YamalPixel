class Plugin():
    def __init__(self):
        super().__init__()
        self.buttons = []  # Храним ссылки на созданные кнопки

    def on_enable(self):
        print(f"[{self.name}] Активирован!")

        # Проверяем, не созданы ли уже кнопки
        if hasattr(self, '_buttons_created') and self._buttons_created:
            return

        # Создаем кнопки
        btn1 = self.api.add_button(
            self.id,
            "Кнопка 1",
            self.on_button1_click,
            position='top'
        )

        btn2 = self.api.add_button(
            self.id,
            "Кнопка 2",
            self.on_button2_click,
            position='bottom'
        )

        if btn1:
            self.buttons.append(btn1)
        if btn2:
            self.buttons.append(btn2)

        self._buttons_created = True

    def on_disable(self):
        print(f"[{self.name}] Деактивирован")
        self._buttons_created = False
        self.buttons.clear()

    def on_button1_click(self):
        print("Кнопка 1 нажата")

    def on_button2_click(self):
        print("Кнопка 2 нажата")