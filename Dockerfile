FROM python:3.12 AS converter

ARG ROUND_NUMBER
ARG CIRCUIT_COUNTRY

WORKDIR /app

COPY converter/requirements.txt .
COPY converter/countries.json .

RUN pip install --no-cache-dir -r requirements.txt

COPY converter/main.py .

RUN python3 main.py $ROUND_NUMBER $CIRCUIT_COUNTRY

FROM rust:alpine3.19 AS chef

RUN apk add --no-cache musl-dev pkgconfig openssl-dev

RUN cargo install cargo-chef

WORKDIR /app
RUN cargo new --bin updater
WORKDIR /app/updater

COPY updater/Cargo.toml .

FROM chef AS planner

RUN cargo chef prepare --recipe-path recipe.json

FROM planner AS builder

COPY --from=planner /app/updater/recipe.json recipe.json
# Build dependencies - this is the caching Docker layer!
RUN cargo chef cook --release --recipe-path recipe.json

COPY updater/src src

RUN cargo build --release

FROM alpine:3.19 AS runtime

LABEL maintainer="Thibault C. <thibault.chene23@gmail.com>"

COPY --from=builder /app/updater/target/release/updater /usr/local/bin
COPY --from=converter /app/csv /etc/csv

ENTRYPOINT ["/usr/local/bin/updater"]
