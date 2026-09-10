FROM python:3.12-slim

WORKDIR /app

# libs de sistema que o matplotlib pede pra renderizar (mesmo sem display)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6 libpng16-16 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY professor/ professor/
COPY backend/ backend/

EXPOSE 8000
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
