
"""NCBI Protein record retrieval and annotation extraction."""

import re

import requests


NCBI_EFETCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
)
REQUEST_TIMEOUT = 15


def fetch_protein_record(accession: str) -> dict:
    """Fetch an NCBI protein record using its accession.

    Raises:
        ValueError: If the accession is empty.
        RuntimeError: If NCBI cannot return a valid protein record.
    """
    if not accession or not accession.strip():
        raise ValueError("A protein accession is required.")

    accession = accession.strip()

    try:
        response = requests.get(
            NCBI_EFETCH_URL,
            params={
                "db": "protein",
                "id": accession,
                "rettype": "gb",
                "retmode": "text",
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            f"NCBI protein lookup failed for {accession}."
        ) from exc

    record_text = response.text or ""

    # NCBI returns an error document or an empty response for some
    # invalid identifiers. Do not mistake either for a protein record.
    if not re.search(r"(?m)^LOCUS\s+", record_text):
        raise RuntimeError(
            f"NCBI returned no valid protein record for {accession}."
        )

    version_match = re.search(
        r"(?m)^VERSION\s+(\S+)", record_text
    )
    accession_match = re.search(
        r"(?m)^ACCESSION\s+(\S+)", record_text
    )

    resolved_accession = (
        version_match.group(1)
        if version_match
        else accession_match.group(1)
        if accession_match
        else accession
    )

    description_match = re.search(
        r"(?ms)^DEFINITION\s+(.+?)(?=\n[A-Z][A-Z ]{1,11}\s|\Z)",
        record_text,
    )
    description = ""
    if description_match:
        description = " ".join(
            line.strip()
            for line in description_match.group(1).splitlines()
        ).strip()

    organism_match = re.search(
        r"(?m)^  ORGANISM\s+(.+)$", record_text
    )
    organism = (
        organism_match.group(1).strip()
        if organism_match
        else None
    )

    localization_annotations = []

    # Only accept explicit localization fields. Do not interpret
    # arbitrary COMMENT text, protein names, or sequence features
    # as proof of a cellular location.
    localization_patterns = (
        r'(?im)^\s*/subcellular_location\s*=\s*"([^"]+)"',
        r'(?im)^\s*/note\s*=\s*"SUBCELLULAR LOCATION:\s*([^"]+)"',
    )

    for pattern in localization_patterns:
        for match in re.finditer(pattern, record_text):
            location = match.group(1).strip()
            if location and location not in {
                item["location"] for item in localization_annotations
            }:
                localization_annotations.append(
                    {
                        "location": location,
                        "evidence_codes": [],
                    }
                )

    return {
        "source": "NCBI Protein",
        "accession": resolved_accession,
        "protein_name": description or None,
        "organism": organism,
        "localization_annotations": localization_annotations,
        "localization_status": (
            "available"
            if localization_annotations
            else "no_annotations"
        ),
    }
