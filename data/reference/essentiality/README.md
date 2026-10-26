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