FROM python:3.12 AS converter

ARG ROUND_NUMBER
ARG CIRCUIT_COUNTRY

WORKDIR /app

COPY converter/requirements.txt .
COPY converter/countries.json .

RUN pip install --no-cache-dir -r requirements.txt

COPY converter/main.py .

RUN python3 main.py $ROUND_NUMBER $CIRCUIT_COUNTRY
