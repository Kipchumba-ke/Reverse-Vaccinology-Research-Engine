#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MAKEBLASTDB="${MAKEBLASTDB_EXECUTABLE:-$(command -v makeblastdb || true)}"

if [[ -z "$MAKEBLASTDB" ]]; then
    if [[ -x "$HOME/micromamba/bin/makeblastdb" ]]; then
        MAKEBLASTDB="$HOME/micromamba/bin/makeblastdb"
    else
        echo "Error: makeblastdb was not found." >&2
        echo "Install BLAST+ or set MAKEBLASTDB_EXECUTABLE." >&2
        exit 1
    fi
fi

build_database() {
    local host="$1"
    local fasta="$2"
    local database="$3"

    echo "Building ${host} protein database..."

    if [[ ! -s "$PROJECT_ROOT/$fasta" ]]; then
        echo "Error: FASTA file missing or empty: $fasta" >&2
        exit 1
    fi

    "$MAKEBLASTDB" \
        -in "$PROJECT_ROOT/$fasta" \
        -dbtype prot \
        -parse_seqids \
        -out "$PROJECT_ROOT/$database"

    if [[ ! -s "$PROJECT_ROOT/${database}.pin" ]]; then
        echo "Error: Expected database index was not created: ${database}.pin" >&2
        exit 1
    fi

    echo "Finished building ${host} database."
}

build_database \
    "human" \
    "data/reference/human/human_reference_proteome.fasta" \
    "data/reference/human/human_proteome_db"

build_database \
    "mouse" \
    "data/reference/mouse/mouse_reference_proteome.fasta" \
    "data/reference/mouse/mouse_proteome_db"

build_database \
    "pig" \
    "data/reference/pig/pig_reference_proteome.fasta" \
    "data/reference/pig/pig_proteome_db"

echo "All host BLAST databases built successfully."
