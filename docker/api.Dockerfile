# API container: uvicorn serving the Model Gateway + RAG + Agent + RBAC platform.
# Runtime data (SQLite + Chroma) is mounted as a volume, never baked into the image.
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev --no-install-project

COPY app ./app
COPY data/documents ./data/documents
COPY data/synthetic ./data/synthetic
RUN mkdir -p ./data/runtime

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
