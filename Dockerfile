# Retain a Python version compatible with this legacy Django application.
FROM python:3.8-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /code

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libffi-dev libssl-dev libpq-dev libjpeg-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements*.txt /code/
RUN python -m pip install "pip<25" "setuptools<70" "wheel<0.46" \
    && pip install -r requirements.txt

COPY . /code/
