FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir \
    -i https://mirror.abrha.net/repository/pypi/simple \
    --trusted-host mirror.abrha.net \
    -r requirements.txt

COPY . /app/

EXPOSE 8000
