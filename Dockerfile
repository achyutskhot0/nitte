FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY . .

# System deps for spaCy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -r ingest/requirements-ingest.txt \
    && pip install -r classifier/requirements-clf.txt \
    && pip install -r extraction/requirements-extract.txt \
    && pip install -r requirements.txt \
    && python -m spacy download en_core_web_sm

EXPOSE 8000
CMD ["uvicorn","glue:app","--host","0.0.0.0","--port","8000"]
