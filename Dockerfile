FROM python:3.10-slim-bullseye

# Устанавливаем только самые нужные инструменты
RUN apt-get update && apt-get install -y git g++ libssl-dev zlib1g-dev make

# Собираем zsign вообще без флагов оптимизации — так безопаснее всего для памяти хостинга
RUN git clone https://github.com/zhlynn/zsign.git \
    && cd zsign \
    && g++ *.cpp -lcrypto -lz -o zsign \
    && cp zsign /usr/local/bin/

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
