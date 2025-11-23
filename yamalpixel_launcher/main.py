# main.py
import sys
import signal
from core.app_context import LauncherApp


def main():
    try:
        # Создаем приложение
        app = LauncherApp()

        # Настраиваем обработчики сигналов для корректного завершения
        signal.signal(signal.SIGINT, app.graceful_shutdown)
        signal.signal(signal.SIGTERM, app.graceful_shutdown)

        # Запускаем приложение
        app.run()

    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()