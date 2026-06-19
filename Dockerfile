FROM python:3.10-slim

# Установлюємо тільки інструменти для скачування та розпаковки
RUN apt-get update && apt-get install -y wget tar && rm -rf /var/lib/apt/lists/*

# Скачуємо ГОТОВИЙ статичний бінарник zsign, який зібрали самі розробники.
# Він важить всього 2 МБ, скачається за секунду і запуститься без навантаження на пам'ять Render.
RUN wget https://github.com/zhlynn/zsign/releases/latest/download/zsign-linux-musl-static.tar.gz \
    && tar -xzf zsign-linux-musl-static.tar.gz \
    && mv zsign /usr/local/bin/zsign \
    && chmod +x /usr/local/bin/zsign \
    && rm zsign-linux-musl-static.tar.gz

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
