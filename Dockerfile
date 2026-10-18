FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8080
WORKDIR /app
COPY requirements-runtime.txt .
RUN pip install --no-cache-dir -r requirements-runtime.txt "uvicorn[standard]"
COPY safeground ./safeground
COPY web ./web
COPY data/snapshot ./data/snapshot
COPY data/cache ./data/cache
CMD exec uvicorn safeground.api.app:app --host 0.0.0.0 --port ${PORT}
