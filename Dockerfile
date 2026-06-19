FROM python:3.10-slim

# Устанавливаем все нужные библиотеки (добавили zlib1g-dev)
RUN apt-get update && apt-get install -y git g++ libssl-dev zlib1g-dev make

# Компилируем БЕЗ тяжелой оптимизации (-O3), чтобы не перегружать память Render
# И добавляем флаг -lz
RUN git clone https://github.com/zhlynn/zsign.git \
    && cd zsign \
    && g++ *.cpp -lcrypto -lz -o zsign \
    && cp zsign /usr/local/bin/

WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt

CMD ["python", "app.py"]

