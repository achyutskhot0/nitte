# Legal Lens – Zero-Dollar Legal Document Analysis Stack

## Quickstart

```bash
# Train classifier (optional initially)
python classifier/clf_train.py

# Get a free Together API key
export TOGETHER_KEY=your_key

# Run via Docker
docker-compose up --build

# Open http://localhost:8000 and upload PDFs/DOCs
```

If you skip training, the app still works using a keyword fallback classifier.

Health check:

```bash
curl http://localhost:8000/health
```

## Structure

- ingest/: FastAPI upload API, multi-doc, any format
- classifier/: 5-min train, ONNX-less quick infer via joblib
- extraction/: spaCy + regex fields
- summarisers/: Lawyer and Citizen JSON summaries via Together
- nextsteps/: Dates and entities
- frontend/: Vanilla JS, 3 tabs
- glue.py: Orchestrates modules
- docker-compose.yml / Dockerfile
