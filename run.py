# run.py
import sys
import os
import signal
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# Добавляем путь с учетом onefile
sys.path.insert(0, resource_path("."))

print("=== STARTUP PHASE 1: Basic imports ===")
sys.stdout.flush()

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
print(f"Path added: {os.path.dirname(os.path.abspath(__file__))}")
sys.stdout.flush()

print("=== STARTUP PHASE 2: Import from Ui ===")
sys.stdout.flush()

try:
    from Ui.MainWindow import run_main_window

    print("✅ MainWindow imported")
    sys.stdout.flush()
except Exception as e:
    print(f"❌ Failed to import MainWindow: {e}")
    import traceback

    traceback.print_exc()
    sys.stdout.flush()
    sys.exit(1)

print("=== STARTUP PHASE 3: Environment setup ===")
sys.stdout.flush()

if __name__ == "__main__":
    print("=== STARTUP PHASE 4: Main block ===")
    sys.stdout.flush()

    # Инициализация ресурсов
    try:
        from ConfDir.Configs import setup_environment

        print("✅ Configs imported")
        sys.stdout.flush()

        setup_environment()
        print("✅ Environment setup complete")
        sys.stdout.flush()
    except Exception as e:
        print(f"❌ Setup environment failed: {e}")
        import traceback

        traceback.print_exc()
        sys.stdout.flush()
        sys.exit(1)

    # Запуск
    print("=== STARTUP PHASE 5: Launching main window ===")
    sys.stdout.flush()
    sys.exit(run_main_window())