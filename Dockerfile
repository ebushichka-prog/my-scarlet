FROM python:3.10-slim
RUN apt-get update && apt-get install -y git g++ libssl-dev make
RUN git clone https://github.com/zhlynn/zsign.git && cd zsign && g++ *.cpp -lcrypto -O3 -o zsign && cp zsign /usr/local/bin/
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
