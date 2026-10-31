# ePath Essentiality Reference Data

## Purpose

This directory contains the local reference data used by the ePath essentiality
evidence integration. The integration can use these records to retrieve
organism-specific essentiality evidence during protein analysis.

The reference files and generated SQLite database are local data assets.
They are not committed to Git because of their size and because redistribution
permissions have not yet been verified.

## Required reference files

Place the following files in this directory:

- `a_Gene_sort.txt`: gene-level reference data used to build the SQLite index.
- `Combined_KOExpEG.txt`: KO-level experimental essentiality data.
- `Experimental_EG.txt`: experimental essentiality records.

The original `a_Gene_sort.rar` archive may be retained locally if needed to
reconstruct `a_Gene_sort.txt`, but it is not required once the extracted text
file is available.

Obtain the data from its original source. Before redistributing any source
files, verify the applicable licence and terms. Record the source URL, retrieval
date, and any relevant licence information for reproducibility. Do not assume
that public availability permits redistribution.

## Build the local database

Run these commands from the repository root with the project's Python
environment activated.

First, build the gene-level index:

```bash
python -m app.integrations.build_epath_index
```

This reads `a_Gene_sort.txt` and creates `epath.sqlite3` in this directory.

Then import the experimental essentiality records into the same database:

```bash
python -m app.integrations.import_epath_evidence
```

This reads `Combined_KOExpEG.txt` and `Experimental_EG.txt` and adds them to
`epath.sqlite3`. Both commands accept `--database` and `--data-dir` (and the
first accepts `--source`) if your files live elsewhere.

## Point the application at it

By default the application looks for `data/reference/essentiality/epath.sqlite3`,
so you normally set nothing. If you move the database, set
`ESSENTIALITY_EPATH_DB_PATH` to the **`.sqlite3` file**. Do not point it at one
of the source `.txt` files: the report then says the database is not set up.

If the database is missing, analyses still complete; the Evidence section shows
the ePath lookup as not set up. Keep the three source files safe: the database
can be rebuilt from them, but they cannot be re-downloaded from this repository.
