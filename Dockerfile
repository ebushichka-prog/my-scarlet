FROM python:3.10-slim-bullseye

# Установлюємо залежності для збірки
RUN apt-get update && apt-get install -y git g++ libssl-dev zlib1g-dev && rm -rf /var/lib/apt/lists/*

# Клонуємо та компілюємо КОЖЕН файл окремо (-c) з жорстким обмеженням пам'яті для GCC.
# Це єдиний спосіб обійти ліміт у 512 МБ на Render.
RUN git clone https://github.com/zhlynn/zsign.git \
    && cd zsign \
    && for f in *.cpp; do g++ -O0 --param ggc-min-expand=0 --param ggc-min-heapsize=8192 -c "$f"; done \
    && g++ *.o -lcrypto -lz -o zsign \
    && cp zsign /usr/local/bin/zsign \
    && cd .. && rm -rf zsign

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
