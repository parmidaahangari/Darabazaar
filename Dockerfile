FROM python:3.10-slim-bookworm

# اصلاح فرمت متغیرهای محیطی برای رفع وارنینگ‌ها
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# نصب وابستگی‌های سیستم (این بار بدون ارور ۴۰۴ اجرا می‌شود)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000

CMD ["gunicorn", "FirstGame.wsgi:application", "--bind", "0.0.0.0:8000"]