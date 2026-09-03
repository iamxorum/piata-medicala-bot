FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py scraper.py telegram_client.py storage.py ./

CMD ["python", "main.py"]
