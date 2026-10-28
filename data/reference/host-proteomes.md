# Host Proteome Reference Data

## Purpose

This directory contains protein reference datasets used by the reverse-vaccinology application for host-similarity analysis.

The application supports three host references:

- Human: *Homo sapiens*
- Mouse: *Mus musculus*
- Pig: *Sus scrofa*

Reference sequences are stored in FASTA files. BLAST protein databases are generated locally from these files.

## Directory Structure

```text
data/reference/
├── human/
│   └── human_reference_proteome.fasta
├── mouse/
│   ├── mouse_reference_proteome.fasta
│   └── mouse_reference_proteome.candidate.fasta
├── pig/
│   └── pig_reference_proteome.fasta
└── host-proteomes.md
```

Generated BLAST database index files are excluded from Git because they can be rebuilt from the corresponding FASTA files.

## Reference Files and Provenance

| Host | UniProt proteome | FASTA file | Records |
|---|---|---|---:|
| Human | `UP000005640` | `human/human_reference_proteome.fasta` | 169,651 |
| Mouse, active | `UP000000589` | `mouse/mouse_reference_proteome.fasta` | 54,855 |
| Pig | `UP000008227` | `pig/pig_reference_proteome.fasta` | 46,079 |
| Mouse, candidate | `UP000000589` | `mouse/mouse_reference_proteome.candidate.fasta` | 63,328 |

The human and pig reference FASTAs are retrieved from UniProt using their proteome accessions. The existing mouse reference is retained as the active mouse dataset.

The expanded mouse candidate was retrieved from UniProt with isoform inclusion enabled. It contains 8,473 additional identifiers compared with the active mouse reference. The additional identifiers follow an isoform-style pattern.

The candidate has not replaced the active mouse reference. Adoption requires a deliberate reference update followed by appropriate application tests and documentation.

Record counts alone do not establish proteome completeness or equivalence between release versions.

## FASTA Verification

The following SHA-256 checksums were calculated from the local files.

| Reference | FASTA records | SHA-256 |
|---|---:|---|
| Human | 169,651 | `bddb19a7250993b40cb48099139a0fe941462eb4f33acc2691c40039663be358` |
| Mouse, active | 54,855 | `1f3b520e4078f6e5addde6f4d2b8e7307e61ed2be8b71f6af0ad0b2099285caa` |
| Pig | 46,079 | `8a597a719cfed02e71045534b4b5676631a170008cf788ea3fb2f736915f0583` |
| Mouse, candidate | 63,328 | `1caa472043709281c4069a253e29a2e9d3691933e0e88b232c1ac7cbb6ee4f49` |

A BLASTP smoke test against a separately built database from the candidate mouse FASTA returned matches for a query taken from the existing mouse reference.

The checksums identify the exact files verified locally. Retrieval dates and source release identifiers should be recorded when confirmed. Applicable licences and redistribution conditions should also be verified before distributing reference data.

## Requirements

- Python environment for the application.
- NCBI BLAST+ utilities, including `makeblastdb` and `blastp`.
- The reference FASTA files needed for the selected host analyses.

## Downloading Reference FASTAs

From the repository root, run:

```bash
./scripts/download_host_proteomes.sh
```

The script downloads the human and pig FASTAs when their destination files do not already exist. It preserves the existing mouse reference.

To retrieve an expanded mouse candidate separately, run:

```bash
./scripts/download_host_proteomes.sh --download-mouse-candidate
```

The script reports the record count and SHA-256 checksum of each newly downloaded file. Existing destination files are skipped rather than overwritten.

Because UniProt reference data may change over time, a future download is not guaranteed to reproduce the same checksum as the files documented above. Compare the resulting checksums and record counts before adopting a changed dataset.

## Building BLAST Databases

After the required FASTA files are available, run:

```bash
./scripts/build_host_blast_databases.sh
```

The script builds these database prefixes:

| Host | Database prefix |
|---|---|
| Human | `data/reference/human/human_proteome_db` |
| Mouse | `data/reference/mouse/mouse_proteome_db` |
| Pig | `data/reference/pig/pig_proteome_db` |

The script looks for `makeblastdb` on `PATH` and also checks the default location under `~/micromamba/bin/`.

If it is installed elsewhere, configure its location:

```bash
export MAKEBLASTDB_EXECUTABLE="/path/to/makeblastdb"
```

The FASTA files must exist before the build script is run.

## Application Configuration

The application supports the following environment variables:

```bash
HOST_BLAST_DATABASE_HUMAN=/path/to/human_proteome_db
HOST_BLAST_DATABASE_MOUSE=/path/to/mouse_proteome_db
HOST_BLAST_DATABASE_PIG=/path/to/pig_proteome_db
```

Each value is a BLAST database prefix, not the FASTA path or an individual index file.

When a host-specific variable is not configured, the application can use the corresponding local database if available.

The legacy `HOST_BLAST_DATABASE` setting remains available for compatibility with callers that do not specify a host reference.

Selecting `none` disables host-similarity searching.

## Reproducibility and Maintenance

For each reference dataset, maintain the source URL, proteome accession, retrieval date or release when available, file size, SHA-256 checksum, and applicable licence or redistribution conditions.

Keep generated BLAST database files out of version control. Rebuild them from the appropriate FASTA files when setting up a new environment.

The human and pig FASTAs and expanded mouse candidate are large local data files and should not be added to ordinary Git history without an explicit decision about data distribution. The download script provides a retrieval path for these files. The existing mouse FASTA remains the active reference unless a deliberate change is made.