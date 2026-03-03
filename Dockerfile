FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .
COPY server.py .

RUN pip install --no-cache-dir fastmcp httpx

CMD ["python", "server.py"]
