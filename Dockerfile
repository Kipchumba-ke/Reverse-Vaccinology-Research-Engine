FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# BLAST+ for host similarity and Clustal Omega for multiple-sequence alignment.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ncbi-blast+ clustalo \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/app

COPY requirements.txt requirements-biolib.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# pybiolib is only needed for DeepTMHMM or SignalP through BioLib.
#   docker compose --profile app build --build-arg INSTALL_BIOLIB=1
ARG INSTALL_BIOLIB=0
RUN if [ "$INSTALL_BIOLIB" = "1" ]; then \
        pip install --no-cache-dir -r requirements-biolib.txt; \
    fi

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini.example ./alembic.ini
COPY scripts ./scripts
COPY data/reference/host-proteomes.md ./data/reference/host-proteomes.md

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# Run the API. For the background worker, override the command with:
#   celery -A app.services.celery_queue.celery_app worker --loglevel=info
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "app:create_app()"]
