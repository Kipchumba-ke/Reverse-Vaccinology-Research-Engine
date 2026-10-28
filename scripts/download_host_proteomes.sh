#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MOUSE_CANDIDATE=false

usage() {
    cat <<'USAGE'
Usage:
  ./scripts/download_host_proteomes.sh
  ./scripts/download_host_proteomes.sh --download-mouse-candidate

Default:
  Download human and pig proteomes only when their destination files
  do not already exist. Preserve the existing mouse reference.

Options:
  --download-mouse-candidate
      Also download the current UniProt mouse proteome into a separate
      candidate FASTA file. The existing mouse FASTA is not replaced.

  -h, --help
      Show this help message.
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --download-mouse-candidate)
            MOUSE_CANDIDATE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Error: unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
done

download_proteome() {
    local host="$1"
    local proteome_id="$2"
    local relative_destination="$3"
    local destination="$PROJECT_ROOT/$relative_destination"
    local temporary_file
    local url

    if [[ -e "$destination" ]]; then
        echo "Skipping ${host}: destination already exists."
        echo "  $relative_destination"
        return 0
    fi

    mkdir -p "$(dirname "$destination")"

    temporary_file="$(mktemp "${destination}.XXXXXX")"

    url="https://rest.uniprot.org/uniprotkb/stream?query=proteome%3A${proteome_id}&format=fasta&compressed=false&includeIsoform=true"

    echo "Downloading ${host} proteome (${proteome_id})..."

    if ! curl --fail --location --silent --show-error \
        --retry 3 \
        --retry-delay 2 \
        "$url" \
        --output "$temporary_file"; then
        rm -f "$temporary_file"
        echo "Error: download failed for ${host}." >&2
        return 1
    fi

    if [[ ! -s "$temporary_file" ]] ||
       ! grep -q '^>' "$temporary_file"; then
        rm -f "$temporary_file"
        echo "Error: downloaded FASTA is empty or invalid for ${host}." >&2
        return 1
    fi

    mv "$temporary_file" "$destination"

    echo "Successfully downloaded ${host}."
    echo "  File: $relative_destination"
    echo "  Protein records: $(grep -c '^>' "$destination")"
    echo "  SHA-256:"
    sha256sum "$destination"
    echo
}

download_proteome \
    "human" \
    "UP000005640" \
    "data/reference/human/human_reference_proteome.fasta"

download_proteome \
    "pig" \
    "UP000008227" \
    "data/reference/pig/pig_reference_proteome.fasta"

if [[ "$MOUSE_CANDIDATE" == true ]]; then
    download_proteome \
        "mouse candidate" \
        "UP000000589" \
        "data/reference/mouse/mouse_reference_proteome.candidate.fasta"
else
    echo "Preserving the existing mouse reference."
    echo "To download a newer mouse candidate, run:"
    echo "  ./scripts/download_host_proteomes.sh --download-mouse-candidate"
fi

echo
echo "Proteome download step completed."
echo "To build the BLAST databases, run:"
echo "  ./scripts/build_host_blast_databases.sh"
