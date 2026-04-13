# Railway / Docker: build vector index *after* the last COPY so Nixpacks-style
# "copy repo over build output" does not wipe data/.lancedb.
FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-install-project

COPY . .

# Must be the last mutating step — no COPY after this.
RUN python src/build_index.py

ENV PORT=8000
EXPOSE 8000

CMD ["python", "main.py"]
