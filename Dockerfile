FROM python:3.12 AS converter

ARG ROUND_NUMBER
ARG ROUND_NAME
ARG IS_SPRINT

WORKDIR /app

COPY converter/requirements.txt .
COPY converter/countries.json .

RUN pip install --no-cache-dir -r requirements.txt

COPY converter/main.py .

RUN python3 main.py "$ROUND_NAME" $IS_SPRINT

FROM rust:1.79-slim-bullseye AS runtime

RUN apt-get update && apt-get install -y libssl-dev
RUN apt update && apt install -y pkg-config

LABEL maintainer="Thibault C. <thibault.chene23@gmail.com>"

WORKDIR /updater
COPY --from=converter /app/csv /etc/csv

COPY updater/Cargo.toml .
COPY updater/src src

RUN cargo build --release
