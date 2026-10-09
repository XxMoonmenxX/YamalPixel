import requests
import socket
import subprocess
import os

print("=== ДИАГНОСТИКА ===")

# 1. Проверка системного прокси
print(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY', 'не установлен')}")
print(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY', 'не установлен')}")

# 2. Проверка DNS
try:
    ip = socket.gethostbyname('launchermeta.mojang.com')
    print(f"DNS launchermeta.mojang.com -> {ip}")
except:
    print("❌ DNS не работает")

# 3. Проверка соединения через requests
try:
    response = requests.get('https://launchermeta.mojang.com/mc/game/version_manifest_v2.json', timeout=10)
    print(f"✅ HTTP работает! Статус: {response.status_code}")
except Exception as e:
    print(f"❌ HTTP не работает: {e}")

# 4. Проверка через curl
try:
    result = subprocess.run(['curl', '-I', 'https://launchermeta.mojang.com/mc/game/version_manifest_v2.json'], capture_output=True, text=True, timeout=10)
    print(f"Curl результат: {result.returncode}")
    if result.returncode == 0:
        print("✅ Curl работает!")
    else:
        print(f"❌ Curl не работает: {result.stderr[:100]}")
except:
    print("❌ Curl не установлен")

# 5. Ваш IP
try:
    response = requests.get('https://api.ipify.org', timeout=10)
    print(f"Ваш IP: {response.text}")
except:
    print("❌ Не удалось определить IP")