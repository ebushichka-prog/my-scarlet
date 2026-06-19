import os
import sys
import requests
import subprocess
from flask import Flask, request, render_template_string, send_from_directory, jsonify

app = Flask(__name__)

# --- НАСТРОЙКИ ---
PORT = 5000
# Ссылка на постоянно обновляемый репозиторий с бесплатными сертификатами
CERT_REPO = "https://raw.githubusercontent.com/skypere/esign-certificates/main/active_cert.json"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)

# --- АВТОМАТИЧЕСКАЯ ЗАГРУЗКА СЕРТИФИКАТА ---
def update_certificates():
    print("[*] Проверка и загрузка свежих сертификатов...")
    try:
        # Пытаемся получить ссылки на рабочие сертификаты сообщества
        response = requests.get(CERT_REPO, timeout=10).json()
        p12_url = response["p12"]
        mp_url = response["mobileprovision"]
        password = response.get("password", "1")
        
        # Скачиваем файлы
        with open(os.path.join(STORAGE_DIR, "cert.p12"), "wb") as f:
            f.write(requests.get(p12_url).content)
        with open(os.path.join(STORAGE_DIR, "cert.mobileprovision"), "wb") as f:
            f.write(requests.get(mp_url).content)
            
        with open(os.path.join(STORAGE_DIR, "password.txt"), "w") as f:
            f.write(password)
            
        print("[+] Сертификаты успешно обновлены!")
        return True
    except Exception as e:
        print(f"[-] Не удалось обновить сертификаты автоматически: {e}")
        print("[!] Убедитесь, что в папке storage лежат файлы cert.p12 и cert.mobileprovision")
        return False

# --- ШАБЛОН ИНТЕРФЕЙСА (HTML/CSS) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scarlet Cloud Clone</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b0b0c; color: #fff; text-align: center; padding: 20px; }
        .container { max-width: 500px; margin: 50px auto; background: #161618; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        h1 { color: #ff3b30; font-size: 28px; margin-bottom: 5px; }
        p { color: #8e8e93; font-size: 14px; }
        input[type="text"], input[type="file"] { width: 100%; padding: 12px; margin: 15px 0; border-radius: 10px; border: 1px solid #2c2c2e; background: #1c1c1e; color: #fff; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: #ff3b30; border: none; color: white; font-weight: bold; border-radius: 10px; cursor: pointer; font-size: 16px; transition: 0.2s; }
        button:hover { background: #e03228; }
        .footer { margin-top: 30px; font-size: 11px; color: #48484a; }
        #status { margin-top: 15px; color: #00cd4b; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Scarlet Cloud</h1>
        <p>Установка IPA без компьютера и ручного поиска сертификатов</p>
        
        <form action="/sign" method="POST" enctype="multipart/form-data" id="uploadForm">
            <input type="text" name="ipa_url" placeholder="Вставьте прямую ссылку на IPA файл">
            <p>или выберите файл с устройства:</p>
            <input type="file" name="ipa_file" accept=".ipa">
            <button type="submit" id="submitBtn">Подписать и Установить</button>
        </form>
        <div id="status"></div>
    </div>
    <div class="footer">Создано в образовательных целях • 2026</div>

    <script>
        document.getElementById('uploadForm').onsubmit = function() {
            document.getElementById('submitBtn').disabled = true;
            document.getElementById('submitBtn').innerText = 'Подписание... Ждите';
            document.getElementById('status').innerText = 'Процесс пошел. Это может занять до 1-2 минут...';
        };
    </script>
</body>
</html>
"""

# --- МАРШРУТЫ (ROUTES) ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/sign', methods=['POST'])
def sign_ipa():
    # Определение базового URL для OTA ссылки
    server_url = request.url_root.replace("http://", "https://") # iOS строго требует HTTPS
    
    ipa_path = os.path.join(STORAGE_DIR, "input.ipa")
    output_ipa = os.path.join(STORAGE_DIR, "signed.ipa")
    
    # Удаляем старые файлы если они есть
    for f in [ipa_path, output_ipa]:
        if os.path.exists(f): os.remove(f)

    # 1. Получаем IPA (по ссылке или файлом)
    ipa_url = request.form.get("ipa_url")
    ipa_file = request.files.get("ipa_file")

    if ipa_file and ipa_file.filename != '':
        ipa_file.save(ipa_path)
    elif ipa_url:
        try:
            r = requests.get(ipa_url, stream=True, timeout=30)
            with open(ipa_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
        except Exception as e:
            return f"Ошибка скачивания IPA по ссылке: {e}", 400
    else:
        return "Вы не предоставили IPA файл", 400

    # 2. Проверяем наличие утилиты zsign
    if subprocess.call(["which", "zsign"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) != 0:
        return "Ошибка сервера: утилита zsign не установлена!", 500

    # 3. Подписываем файл
    cert = os.path.join(STORAGE_DIR, "cert.p12")
    prov = os.path.join(STORAGE_DIR, "cert.mobileprovision")
    
    with open(os.path.join(STORAGE_DIR, "password.txt"), "r") as f:
        password = f.read().strip()

    # Запуск консольной команды zsign
    cmd = ["zsign", "-k", cert, "-p", password, "-m", prov, "-o", output_ipa, ipa_path]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return f"Ошибка подписания IPA:<br><pre>{result.stderr}</pre>", 500

    # 4. Генерируем ссылку для установки (itms-services)
    manifest_url = f"{server_url}manifest.plist"
    ota_link = f"itms-services://?action=download-manifest&url={manifest_url}"
    
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: sans-serif; text-align: center; padding: 50px; background: #0b0b0c; color: white; }}
            .btn {{ display: inline-block; padding: 15px 30px; background: #00cd4b; color: white; border-radius: 10px; text-decoration: none; font-size: 20px; font-weight: bold; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <h2>Приложение успешно подписано!</h2>
        <a class="btn" href="{ota_link}">НАЖМИ ДЛЯ УСТАНОВКИ</a>
        <br><br>
        <p><a href="/" style="color: #8e8e93;">Назад на главную</a></p>
    </body>
    </html>
    """

@app.route('/manifest.plist')
def manifest():
    server_url = request.url_root.replace("http://", "https://")
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>items</key>
    <array>
        <dict>
            <key>assets</key>
            <array>
                <dict>
                    <key>kind</key>
                    <string>software-package</string>
                    <key>url</key>
                    <string>{server_url}download/signed.ipa</string>
                </dict>
            </array>
            <key>metadata</key>
            <dict>
                <key>bundle-identifier</key>
                <string>com.clone.scarlet.app</string>
                <key>bundle-version</key>
                <string>1.0</string>
                <key>kind</key>
                <string>software</string>
                <key>title</key>
                <string>Scarlet Sideloaded</string>
            </dict>
        </dict>
    </array>
</dict>
</plist>"""
    return plist_content, 200, {'Content-Type': 'application/xml'}

@app.route('/download/signed.ipa')
def download():
    return send_from_directory(STORAGE_DIR, "signed.ipa", as_attachment=True)

if __name__ == '__main__':
    update_certificates()
    # Запуск с adhoc SSL (генерация временного HTTPS)
    app.run(host='0.0.0.0', port=PORT, ssl_context='adhoc')
