# ReverseVax

Oct 29, 2026 · @Kipchumba

**An evidence-compilation platform for reverse vaccinology: it screens pathogen protein sequences and organises the results into an explainable report.**

> **Status:** active development, started 19 September 2026. Not a validated vaccine-candidate predictor.

## Overview

Reverse vaccinology starts from a pathogen's protein sequences, not from laboratory culture, and asks which proteins are worth testing as vaccine targets. ReverseVax takes a protein sequence, runs sequence-level analyses on it, gathers external evidence about it, and returns a report that lists supporting evidence, concerns and missing evidence.

It does **not** produce a vaccine-candidacy score. A candidate is marked `requires_further_review` whenever any evidence is missing or any concern is raised, and `evidence_compiled` only when everything assessed is present and clean. Neither status says a protein is a good vaccine target.

Intended users: students learning bioinformatics, and researchers who want a structured first look at a protein before experiments.

## Current status

Most analysis modules exist and are unit-tested. The built-in predictors are simple rule-based screens written for this project; they are not the established tools of the same name.

| Capability | Status | What it actually does |
| --- | --- | --- |
| Sequence properties | Implemented | Composition, molecular weight, isoelectric point, GRAVY, net charge |
| Hydropathy and transmembrane candidates | Implemented (heuristic) | Kyte-Doolittle sliding window (19 residues, cutoff 1.6); regions of 18–25 residues are flagged, and regions inside a predicted signal peptide are re-labelled `signal_peptide_h_region` |
| Signal peptide | Implemented (heuristic) + optional SignalP 6.0 | Rule-based screen: charged N-region, hydrophobic core, small residues at the cleavage site (von Heijne -3/-1 rule). The SignalP 6.0 adapter (local install) is off by default |
| Antigenic regions | Implemented (heuristic) | Kolaskar-Tongaonkar propensity scale over a 7-residue window. A scale-based screen, not B-cell or T-cell epitope prediction |
| Epitope and MHC prediction | Optional (IEDB), off by default | `IEDB_ENABLED=1` sends the sequence to the IEDB Analysis Resource for MHC class I and II binding over a configurable HLA allele panel and linear B-cell epitopes (Bepipred-2.0). Results are predictions, with percentile ranks |
| Peptide windows | Implemented | 15-residue windows with GRAVY, charge, antigenic propensity and overlap flags (`app/analysis/peptide_windows.py`) |
| Conservation | Implemented | Identity per column plus similarity groups (Clustal-style strong/weak). Uses Clustal Omega when installed, otherwise a built-in star alignment scored with BLOSUM62 |
| Host similarity | Implemented | BLASTP against local human, mouse or pig proteome databases; interpretation thresholds are configurable |
| Short-peptide host scan | Implemented, off by default | `HOST_PEPTIDE_SCAN=1` searches peptide windows with BLAST short-query settings and reports matches of 8+ identical residues |
| Subcellular localization | Database evidence + optional predictors | Records locations from UniProt or NCBI annotations. Optional DeepTMHMM (BioLib cloud) and PSORTb 3.0 (local or Docker install) add predicted compartments as evidence, and the assessment flags when tools agree or conflict. A low-confidence topology hint from the built-in screens is kept apart from evidence |
| Sequence map and 3-D structure | Implemented | Frontend feature map, MHC heatmaps, and a rotatable backbone view of the AlphaFold DB model when the protein has a UniProt accession. No structure prediction is run |
| Essentiality | Evidence intake only | Looks up a local ePath database that you must build yourself |
| Candidate assessment | Implemented | Sorts evidence into supporting, concerns and missing; no score |
| Report and PDF export | Implemented | Structured report per analysis, downloadable as PDF |
| Accounts and history | Implemented | Register, login, per-user history, delete; owner-only access |
| Background jobs | Wired, needs setup | Celery and Redis queue; requires a running worker |
| TMHMM 2.0, BepiPred-3.0, NetMHC standalone, ESMFold | Not integrated | TMHMM and BepiPred-3.0 have no public API and licensed downloads; see roadmap |

## How it works

A submitted sequence passes through the steps below. Steps marked optional run only when their inputs or reference data are available.

1. **Validate.** Whitespace is stripped, letters are upper-cased, and anything outside the 20 standard amino acids is rejected.
2. **Compute properties.** Composition, molecular weight, isoelectric point, GRAVY and charge.
3. **Find hydrophobic and transmembrane candidates** with the Kyte-Doolittle window.
4. **Screen for a signal peptide and antigenic regions**, re-label hydrophobic regions that are really signal-peptide cores, and derive a low-confidence localization hint.
5. **Slide 15-residue peptide windows** and flag overlaps with transmembrane and antigenic regions.
6. **Conservation (optional).** With `msa_sequences`, the sequences are aligned and each column is scored for identity, similarity group and gaps.
7. **Host similarity (optional).** BLASTP against the chosen host proteome (`human`, `mouse`, `pig`), or skipped with `none`. With `HOST_PEPTIDE_SCAN=1`, peptide windows are also searched with short-query settings.
8. **External evidence and predictors (optional).** Localization from UniProt or NCBI annotations; essentiality from the local ePath database; signal peptide, topology and localization from SignalP 6.0, DeepTMHMM and PSORTb if enabled; MHC and B-cell epitope predictions from IEDB if enabled.
9. **Assess.** Evidence is sorted into supporting, concerns and missing, and a status is set.
10. **Report.** The result is stored and can be downloaded as JSON or PDF.

External lookups fail soft: if UniProt, NCBI or BLAST is unavailable, that evidence is reported as missing rather than the whole analysis failing.

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Python 3.12, Flask 3, flask-cors |
| Bioinformatics | NCBI BLAST+ (`blastp`, `makeblastdb`), Clustal Omega (`clustalo`, optional locally, installed in the Docker image) |
| Data | PostgreSQL 16, SQLAlchemy 2, Alembic |
| Jobs | Celery, Redis 7 |
| Auth | PyJWT (HS256), Werkzeug password hashing |
| Reports | ReportLab (PDF) |
| Frontend | React 19, Vite, React Router; tests with Vitest and Testing Library |
| Backend tests | pytest |
| CI | GitHub Actions (backend, frontend, Docker build) |

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

This starts only the database and Redis, so you can run the Flask app, Celery worker and frontend on your machine as in step 6.

To run the whole stack in containers instead (migrations, API, worker and an nginx-served frontend at `http://localhost:8080`):

```bash
export JWT_SECRET_KEY="$(openssl rand -hex 32)"
docker compose --profile app up --build
```

The host BLAST databases under `./data/reference` are mounted read-only. Build them first (step 5).

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
| `JWT_EXPIRES_MINUTES` | Token lifetime (default 1440). Tokens without an expiry are rejected |
| `RATE_LIMIT_*`, `TRUSTED_PROXY_COUNT` | Rate limits and proxy depth; see `.env.example` |
| `MAX_SEQUENCE_LENGTH`, `MAX_FASTA_RECORDS`, `MAX_ALIGNMENT_CELLS`, `MAX_REQUEST_BYTES` | Input caps |
| `ALIGNMENT_SCORING` | `blosum62` (default) or `identity` for the built-in aligner |
| `HOST_SIMILARITY_*`, `HOST_PEPTIDE_*` | Host-similarity thresholds and the short-peptide scan |
| `SIGNALP_ENABLED`, `SIGNALP_BACKEND`, `SIGNALP6_EXECUTABLE`, `SIGNALP_BIOLIB_APP`, `SIGNALP_ORGANISM` | Optional SignalP 6.0 adapter. `SIGNALP_BACKEND` is `local` (default, your own `signalp6` install) or `biolib` (cloud app through `pybiolib`; sends the sequence to BioLib) |
| `DEEPTMHMM_ENABLED` | Optional DeepTMHMM through BioLib; needs `pip install pybiolib` and sends the sequence to BioLib |
| `PSORTB_ENABLED`, `PSORTB_EXECUTABLE`, `PSORTB_GRAM` | Optional PSORTb 3.0 from a local or Docker install (`negative`, `positive` or `archaea`) |
| `IEDB_ENABLED`, `IEDB_MHCI_ALLELES`, `IEDB_MHCII_ALLELES`, `IEDB_MHCI_LENGTH`, `IEDB_MHCII_LENGTH`, `IEDB_MHCI_RANK_CUTOFF`, `IEDB_MHCII_RANK_CUTOFF`, `IEDB_MAX_SEQUENCE_LENGTH`, `IEDB_API_BASE` | Optional IEDB epitope and MHC prediction; sends the sequence to IEDB |

Copy `.env.example` as a starting point. `JWT_SECRET_KEY` is required: the app refuses to issue or verify tokens without it.

### 4. Create the database tables

Migrations are in `migrations/versions/`. `alembic.ini` is git-ignored, so copy the template first (the Docker image does this for you):

```bash
cp alembic.ini.example alembic.ini
```

Then run:

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

The frontend runs at `http://localhost:5173`, the default allowed origin. Set `CORS_ALLOWED_ORIGINS` to allow others.

If a token expires or is rejected, the frontend clears it and returns to the login page.

**Rate limits.** Requests are limited per IP (300/minute by default), login and registration more tightly (10/minute per IP), and analysis submissions per user (30/hour). Limited requests get `429` with a `Retry-After` header. Counters are held in memory per worker unless `RATE_LIMIT_STORAGE_URL` points at Redis. Behind a reverse proxy, set `TRUSTED_PROXY_COUNT` so the real client IP is used. `GET /api/health` reports liveness.

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

`GET /api/structure/<accession>` (authenticated) returns the AlphaFold DB model for a UniProt accession: the PDB text, per-residue pLDDT, mean pLDDT and the model's reference sequence. It returns `400` for something that is not a UniProt accession, `404` when AlphaFold DB has no model, and `502` when AlphaFold DB cannot be reached.

When a predictor is enabled, the report gains a `prediction_status` object with one entry per predictor attempted (`completed`, `lookup_failed` or `not_performed`). Predictor output sits under `measurements.sequence_predictions` (`signalp`, `deeptmhmm`, `psortb`, `epitopes`); predicted compartments also appear in `evidence.localization` with the tool as the source.

### Optional predictors

Every predictor is off by default and fails soft: a missing install or an unreachable service is reported in `prediction_status` and the rest of the analysis still runs.

| Tool | How it runs | Data leaves your server? | Licence |
| --- | --- | --- | --- |
| SignalP 6.0 | `local`: your own `signalp6` install. `biolib`: BioLib cloud app `DTU/SignalP_6` through `pybiolib` | `local`: No. `biolib`: Yes, to BioLib | DTU licence (free for academic use, not redistributable); BioLib terms for `biolib` |
| DeepTMHMM | BioLib cloud app `DTU/DeepTMHMM` through `pybiolib` | Yes, to BioLib | BioLib and DTU terms |
| PSORTb 3.0 | Local `psort`, for example the `brinkmanlab/psortb_commandline` Docker image | No | Open source |
| IEDB MHC and B-cell | IEDB Analysis Resource REST API | Yes, to IEDB | IEDB terms |
| AlphaFold DB model | EMBL-EBI public API, fetched when you click "Load predicted 3-D structure" | Only the accession | CC BY 4.0 |

The provided Docker image includes BLAST+ and Clustal Omega only. IEDB works in it as is; for SignalP, DeepTMHMM or PSORTb, extend the image (or run the API outside Docker) with the tool or `pybiolib`.

Do not enable the services that send data off your server for unpublished or confidential sequences. These adapters were written against published documentation and tested on hand-written output samples; run one real protein through each before relying on it.

## Project structure

```text
app/
  __init__.py        Flask app factory and all routes
  analysis/          sequence analysis, signal peptide, antigenic regions, topology, conservation, BLAST, assessment
  integrations/      UniProt, NCBI, ePath, Clustal Omega, AlphaFold DB, and optional SignalP, DeepTMHMM, PSORTb, IEDB
  input/             FASTA parsing
  models/            domain objects and SQLAlchemy models
  repositories/      database access
  reporting/         report assembly and PDF export
  services/          analysis workflow, auth, tokens, Celery queue
  utils/             sequence validation, input limits
data/reference/      host proteome FASTA files and provenance notes
frontend/            React + Vite web interface
migrations/          Alembic migration history
scripts/             reference download and BLAST database build
tests/               pytest suite
compose.yaml         Postgres and Redis; full stack with --profile app
.github/workflows/   CI: backend tests, frontend tests, Docker build
```

Scientific code in `app/analysis/` is kept separate from HTTP and database code, which makes it easy to unit-test. Routes currently still manage the database session themselves; moving that into services is on the roadmap.

## Testing

The backend has 636 pytest test functions across 40 files, covering analysis modules, conservation, BLAST handling, authentication, ownership checks and the API. The frontend has 98 Vitest suites for components and services.

```bash
# Backend (set JWT_SECRET_KEY and, for database tests, TEST_DATABASE_URL)
python -m pytest -q

# Frontend
cd frontend && npm test
```

Tests that touch BLAST need BLAST+ installed. GitHub Actions runs both suites and builds the Docker images on every push and pull request (`.github/workflows/ci.yml`). The test counts above predate the latest changes and are recomputed by CI.

## Limitations and scientific disclaimer

ReverseVax is for education and research. Its output is a structured set of observations, not a recommendation to develop a vaccine.

- **Heuristics, not the established tools.** Transmembrane candidates, signal peptides and antigenic regions come from simple rules written for this project. They are not TMHMM, DeepTMHMM, SignalP or BepiPred, have not been benchmarked, and should not be reported as their output. Expect missed lipoprotein and Tat signal peptides and false positives in hydrophobic proteins.
- **Epitope and MHC results are predictions from a third party.** With IEDB enabled, MHC binding covers a fixed allele panel (not a population's HLA diversity) and a provisional percentile-rank cut-off, and B-cell results are linear epitopes only. None of it shows that a peptide is processed, presented, recognised or immunogenic. Without IEDB, the antigenic-region screen is a linear propensity scale and nothing here models MHC binding.
- **The 3-D view is a prediction, and only for proteins with a UniProt accession.** It draws a backbone trace of the AlphaFold model, not side chains or secondary structure. Regions with pLDDT below 70 are low confidence, and the model describes the UniProt reference sequence, which may differ from the one you analysed (the viewer warns when it does).
- **Localization and essentiality are borrowed or predicted by third parties.** Without a predictor enabled, localization evidence reflects UniProt or NCBI records and is missing for proteins without them. DeepTMHMM's compartment assumes a Gram-negative bacterium. The topology hint is a low-confidence guess from the built-in heuristics, kept apart from evidence.
- **Conservation depends on the alignment.** Similarity groups go beyond exact identity, but the built-in fallback aligner is a star alignment against the first sequence and is weaker than Clustal Omega. Meaning also depends on which sequences you supply.
- **Host-similarity thresholds are provisional.** The defaults (70% identity, 80% coverage, 30% moderate) are screening conventions with no benchmark behind them. They are configurable and printed in every report. The optional short-peptide scan finds identical stretches of 8 or more residues; a clean result does not show a peptide is absent from the host.
- **External adapters are unverified against live services.** SignalP, DeepTMHMM, PSORTb and IEDB are tested on hand-written output samples. The IEDB page does not document its response columns, so the parser matches columns by name and reports what it found if one is missing.
- **Not validated.** The pipeline has not been tested against known vaccine antigens.
- **Reference data varies by release.** Proteome versions and isoform choices change results; the mouse reference has an unadopted candidate with 8,473 extra isoform-style identifiers.

Nothing here establishes immunogenicity, protection, safety or clinical suitability. Any candidate needs expert review and experimental validation.

## Roadmap

**Next: correctness and hygiene**

- [x] Use one database session per request instead of one shared session
- [x] Add an expiry to login tokens, rate limiting, input caps and 401 handling
- [x] Add CI to run both test suites
- [ ] Remove committed `.pyc` and `.save` files; move the large mouse FASTA out of git

**Then: science**

- [x] Optional SignalP adapter and built-in signal peptide screen
- [x] Rename the peptide-window module so it is not mistaken for epitope prediction
- [x] Optional DeepTMHMM, PSORTb and IEDB (MHC-I, MHC-II, B-cell) adapters
- [x] AlphaFold DB structure viewer coloured by confidence and predicted features
- [ ] Verify the SignalP, DeepTMHMM, PSORTb and IEDB adapters against live services
- [ ] Population-coverage-aware HLA panels and a benchmark of MHC cut-offs
- [ ] Structure prediction for proteins with no accession (for example ESMFold)
- [ ] Residue-level epitope and surface mapping on the 3-D structure
- [ ] Benchmark on known vaccine antigens and publish the results
- [ ] Cite and justify every threshold

**Then: product**

- [x] Add app, worker and frontend services to Docker Compose
- [ ] Add screenshots and a demo dataset
- [ ] Publish a machine-readable API specification

## License, contributing and author

**License:** MIT.

**Contributing:** open an issue first for larger changes. Keep scientific code free of HTTP and database dependencies, add tests for changed behaviour, and document any new threshold, tool or reference dataset with its source. Reference data may have its own licence; do not commit it without checking.

**Author:** Kelvin Kipchumba, Nursing and Public Health graduate (Kenyatta University) with software engineering training from Moringa School. [GitHub](https://github.com/Kipchumba-ke) · [LinkedIn](https://linkedin.com/in/kelvin-kipchumba-1b450130b)

Built on Biopython, NCBI BLAST+, UniProt, Flask, React and the open-source community behind them.
