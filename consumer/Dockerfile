FROM python:3.12-slim

WORKDIR /app

COPY consumer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY consumer/app ./app
COPY shared ./shared

ENV PYTHONPATH=/app

CMD ["python", "-m", "app.main"]
