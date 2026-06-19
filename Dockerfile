# Используем версию Bullseye — тут старая добрая OpenSSL 1.1.1, с которой zsign дружит
FROM python:3.10-slim-bullseye

# Устанавливаем инструменты сборки
RUN apt-get update && apt-get install -y git g++ libssl-dev zlib1g-dev make

# Клонируем и собираем zsign с флагом -O0 (ноль оптимизации = минимум потребления ОЗУ)
RUN git clone https://github.com/zhlynn/zsign.git \
    && cd zsign \
    && g++ *.cpp -lcrypto -lz -O0 -o zsign \
    && cp zsign /usr/local/bin/

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]


