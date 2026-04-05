# Railway / Docker: build vector index *after* the last COPY so Nixpacks-style
# "copy repo over build output" does not wipe data/.lancedb.
FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Must be the last mutating step — no COPY after this.
RUN python src/build_index.py

ENV PORT=8000
EXPOSE 8000

CMD ["python", "main.py"]
