# syntax=docker/dockerfile:1.4
FROM python:3.10.8-slim

ADD https://storage.googleapis.com/berglas/main/linux_amd64/berglas /usr/local/bin/berglas
RUN chmod +x /usr/local/bin/berglas

WORKDIR /app

ENTRYPOINT ["/app/docker-entrypoint.sh"]

RUN pip install -U pip poetry==1.3.2

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false --local && \
    poetry install -v

COPY --link ./ /app/
