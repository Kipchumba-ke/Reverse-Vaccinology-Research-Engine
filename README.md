# ReverseVax

Oct 29, 2026 · @Kipchumba

**An evidence-compilation platform for reverse vaccinology: it screens pathogen protein sequences and organises the results into an explainable report.**

> **Status:** active development, started 19 September 2026. Not a validated vaccine-candidate predictor.

## Overview

Reverse vaccinology starts from a pathogen's protein sequences, not from laboratory culture, and asks which proteins are worth testing as vaccine targets. ReverseVax takes a protein sequence, runs sequence-level analyses on it, gathers external evidence about it, and returns a report that lists supporting evidence, concerns and missing evidence.

It does **not** produce a vaccine-candidacy score. A candidate is marked `requires_further_review` whenever any evidence is missing or any concern is raised, and `evidence_compiled` only when everything assessed is present and clean. Neither status says a protein is a good vaccine target.

Intended users: students learning bioinformatics, and researchers who want a structured first look at a protein before experiments.

## Current status

Most analysis modules exist and are unit-tested, but several only organise evidence from outside sources and do not predict anything themselves.

| Capability | Status | What it actually does |
| --- | --- | --- |
| Sequence properties | Implemented | Composition, molecular weight, isoelectric point, GRAVY, net charge |
| Hydropathy and transmembrane candidates | Implemented (heuristic) | Kyte-Doolittle sliding window (19 residues, cutoff 1.6); regions of 18–25 residues are flagged as candidates |
| Peptide windows | Implemented | 15-residue windows with GRAVY, charge and overlap flags. This is not epitope prediction |
| Conservation | Implemented | Exact-identity and consensus per alignment column; needs 2+ sequences and an aligner |
| Host similarity | Implemented | BLASTP against local human, mouse or pig proteome databases |
| Subcellular localization | Evidence intake only | Records locations taken from UniProt or NCBI annotations; no predictor |
| Essentiality | Evidence intake only | Looks up a local ePath database that you must build yourself |
| Candidate assessment | Implemented | Sorts evidence into supporting, concerns and missing; no score |
| Report and PDF export | Implemented | Structured report per analysis, downloadable as PDF |
| Accounts and history | Implemented | Register, login, per-user history, delete; owner-only access |
| Background jobs | Wired, needs setup | Celery and Redis queue; requires a running worker |
| Epitope, signal peptide and antigenicity prediction | Not built | Planned |

## How it works

A submitted sequence passes through the steps below. Steps marked optional run only when their inputs or reference data are available.

1. **Validate.** Whitespace is stripped, letters are upper-cased, and anything outside the 20 standard amino acids is rejected.
2. **Compute properties.** Composition, molecular weight, isoelectric point, GRAVY and charge.
3. **Find hydrophobic and transmembrane candidates** with the Kyte-Doolittle window.
4. **Slide 15-residue peptide windows** and flag overlaps with transmembrane regions.
5. **Conservation (optional).** With `msa_sequences`, the sequences are aligned and each column is scored for identity and gaps.
6. **Host similarity (optional).** BLASTP against the chosen host proteome (`human`, `mouse`, `pig`), or skipped with `none`.
7. **External evidence (optional).** Localization from UniProt or NCBI annotations; essentiality from the local ePath database.
8. **Assess.** Evidence is sorted into supporting, concerns and missing, and a status is set.
9. **Report.** The result is stored and can be downloaded as JSON or PDF.

External lookups fail soft: if UniProt, NCBI or BLAST is unavailable, that evidence is reported as missing rather than the whole analysis failing.

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.12, Flask 3, flask-cors |
| Bioinformatics | Biopython, NCBI BLAST+ (`blastp`, `makeblastdb`), Clustal Omega (`clustalo`) |
| Data | PostgreSQL 16, SQLAlchemy 2, Alembic |
| Jobs | Celery, Redis 7 |
| Auth | PyJWT (HS256), Werkzeug password hashing |
| Reports | ReportLab (PDF) |
| Frontend | React 19, Vite, React Router; tests with Vitest and Testing Library |
| Backend tests | pytest |

## Getting started

**Prerequisites:** Python 3.12, Node.js and npm, Docker, and NCBI BLAST+. Clustal Omega is needed only for multi-sequence conservation.

### 1. Clone and install the backend

```bash
git clone https://github.com/Kipchumba-ke/Reverse-Vaccinology-Research-Engine
cd Reverse-Vaccinology-Research-Engine
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Postgres and Redis

```bash
docker compose up -d
```

This starts only the database and Redis. The Flask app, Celery worker and frontend run on your machine.

### 3. Configure the environment

Create a `.env` file in the repository root. It is git-ignored.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | SQLAlchemy URL for Postgres |
| `JWT_SECRET_KEY` | Signing key for login tokens; use a long random value |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Default to `redis://localhost:6379/0` |
| `BLASTP_EXECUTABLE` | Path to `blastp` if it is not on `PATH` |
| `HOST_BLAST_DATABASE_HUMAN`, `_MOUSE`, `_PIG` | Override the default local BLAST database paths |
| `ESSENTIALITY_EPATH_DB_PATH` | Location of the local ePath SQLite database |
| `TEST_DATABASE_URL` | Database used by the test suite |

### 4. Create the database tables

Migrations are in `migrations/versions/`. `alembic.ini` is git-ignored, so create one first (for example with `alembic init` in a scratch folder, then copy it in). Then run:

```bash
alembic upgrade head
```

### 5. Build the host BLAST databases

```bash
./scripts/download_host_proteomes.sh
./scripts/build_host_blast_databases.sh
```

The FASTA files and checksums are described in `data/reference/host-proteomes.md`. The ePath essentiality data is optional and must be obtained and built separately; see `data/reference/essentiality/README.md`.

### 6. Run it

```bash
# API (application factory)
flask --app "app:create_app" run --debug

# Background worker, in a second terminal
celery -A app.services.celery_queue worker --loglevel=info

# Frontend, in a third terminal
cd frontend && npm install && npm run dev
```

The frontend runs at `http://localhost:5173`, the only origin the API currently allows.

## API reference

All routes except register and login need an `Authorization: Bearer <token>` header; missing or invalid tokens return `401`. Another user's analysis returns `403`.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/api/register` | Create an account from `email` and `password`; returns `201` with `user_id` |
| `POST` | `/api/login` | Returns `user_id` and a `token` |
| `POST` | `/api/analyses` | Queue an analysis; returns `202` with `analysis_id` and status `pending` |
| `GET` | `/api/analyses` | List the signed-in user's analysis history |
| `GET` | `/api/analyses/<id>` | Status, `host_reference` and `report` |
| `DELETE` | `/api/analyses/<id>` | Delete one of your analyses |
| `GET` | `/api/analyses/<id>/report.pdf` | PDF report; only once the analysis is `completed` |
| `POST` | `/api/analyze` | Run an analysis synchronously, from JSON or an uploaded `.fasta`, `.fa` or `.fna` file |

`POST /api/analyses` takes JSON with either `sequence` or `fasta_content` (not both), plus optional `protein_id`, `protein_name`, `organism`, `accession`, `epath_gene_id`, `epath_ko_id` and `host_reference` (`human`, `mouse`, `pig` or `none`).

```bash
curl -X POST http://localhost:5000/api/analyses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"sequence": "MKTAYIAKQRQISFVKSHFSRQ", "host_reference": "human"}'
```

The synchronous `/api/analyze` route also accepts `msa_sequences` for conservation analysis.

## Project structure

```text
app/
  __init__.py        Flask app factory and all routes
  analysis/          sequence analysis, conservation, BLAST, assessment
  integrations/      UniProt, NCBI, ePath essentiality, Clustal Omega
  input/             FASTA parsing
  models/            domain objects and SQLAlchemy models
  repositories/      database access
  reporting/         report assembly and PDF export
  services/          analysis workflow, auth, tokens, Celery queue
  utils/             sequence validation
data/reference/      host proteome FASTA files and provenance notes
frontend/            React + Vite web interface
migrations/          Alembic migration history
scripts/             reference download and BLAST database build
tests/               pytest suite
compose.yaml         Postgres and Redis for development
```

Scientific code in `app/analysis/` is kept separate from HTTP and database code, which makes it easy to unit-test. Routes currently still manage the database session themselves; moving that into services is on the roadmap.

## Testing

The backend has about 590 pytest test functions across 40 files, covering analysis modules, conservation, BLAST handling, authentication, ownership checks and the API. The frontend has Vitest suites for components and services.

```bash
# Backend (set JWT_SECRET_KEY and, for database tests, TEST_DATABASE_URL)
python -m pytest -q

# Frontend
cd frontend && npm test
```

Tests that touch BLAST need BLAST+ installed. No continuous integration is configured yet, so run both suites before each push.

## Limitations and scientific disclaimer

ReverseVax is for education and research. Its output is a structured set of observations, not a recommendation to develop a vaccine.

- **Heuristics, not predictors.** Transmembrane candidates come from a single hydropathy rule and will miss signal peptides and mislabel some regions. They are not a substitute for dedicated tools.
- **No epitope or antigenicity prediction.** Peptide windows carry only GRAVY and charge.
- **Localization and essentiality are borrowed.** They reflect UniProt, NCBI or ePath records, and are missing for proteins without them.
- **Conservation is exact identity.** It does not weigh similar amino acids, and its meaning depends on which sequences you supply.
- **Host similarity thresholds are fixed** (70% identity, 80% coverage) and not yet justified against a benchmark.
- **Not validated.** The pipeline has not been tested against known vaccine antigens.
- **Reference data varies by release.** Proteome versions and isoform choices change results; the mouse reference has an unadopted candidate with 8,473 extra isoform-style identifiers.

Nothing here establishes immunogenicity, protection, safety or clinical suitability. Any candidate needs expert review and experimental validation.

## Roadmap

**Next: correctness and hygiene**

- [ ] Use one database session per request instead of one shared session
- [ ] Add an expiry to login tokens and validate email and password on registration
- [ ] Add CI to run both test suites
- [ ] Remove committed `.pyc` and `.save` files; move the large mouse FASTA out of git

**Then: science**

- [ ] Add real localization and signal peptide prediction through an external tool
- [ ] Replace or rename the peptide-window module, and add real epitope prediction
- [ ] Benchmark on known vaccine antigens and publish the results
- [ ] Cite and justify every threshold

**Then: product**

- [ ] Add app, worker and frontend services to Docker Compose
- [ ] Add screenshots and a demo dataset
- [ ] Publish a machine-readable API specification

## License, contributing and author

**License:** MIT.

**Contributing:** open an issue first for larger changes. Keep scientific code free of HTTP and database dependencies, add tests for changed behaviour, and document any new threshold, tool or reference dataset with its source. Reference data may have its own licence; do not commit it without checking.

**Author:** Kelvin Kipchumba, Nursing and Public Health graduate (Kenyatta University) with software engineering training from Moringa School. [GitHub](https://github.com/Kipchumba-ke) · [LinkedIn](https://linkedin.com/in/kelvin-kipchumba-1b450130b)

Built on Biopython, NCBI BLAST+, UniProt, Flask, React and the open-source community behind them.
