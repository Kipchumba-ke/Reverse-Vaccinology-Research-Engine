
"""Load sourced essentiality evidence from a curated TSV dataset."""

import csv
from pathlib import Path

from app.analysis.essentiality import create_essentiality_evidence


def fetch_essentiality_evidence(
    dataset_path: str | None,
    protein_id: str | None,
    accession: str | None,
    organism: str | None,
) -> dict:
    """Find evidence matching a protein identifier and organism.

    Required TSV columns:
        gene_id, organism, essentiality_status, source,
        confidence, description

    An optional accession column can be used for accession matching.
    """
    if not dataset_path:
        return {
            "evidence": [],
            "status": "not_configured",
            "message": "No essentiality dataset configured.",
        }

    if not organism:
        return {
            "evidence": [],
            "status": "organism_required",
            "message": "Organism is required to match essentiality evidence.",
        }

    path = Path(dataset_path)
    if not path.is_file():
        return {
            "evidence": [],
            "status": "lookup_failed",
            "message": f"Essentiality dataset not found: {path}",
        }

    identifiers = {
        value.strip().casefold()
        for value in (protein_id, accession)
        if value and value.strip()
    }
    target_organism = organism.strip().casefold()

    if not identifiers:
        return {
            "evidence": [],
            "status": "identifier_required",
            "message": "A protein ID or accession is required.",
        }

    evidence = []

    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            required = {
                "gene_id",
                "organism",
                "essentiality_status",
                "source",
                "confidence",
                "description",
            }

            if not reader.fieldnames or not required.issubset(
                set(reader.fieldnames)
            ):
                return {
                    "evidence": [],
                    "status": "lookup_failed",
                    "message": (
                        "Essentiality TSV is missing required columns."
                    ),
                }

            for row in reader:
                row_organism = (row.get("organism") or "").strip()
                gene_id = (row.get("gene_id") or "").strip()
                row_accession = (row.get("accession") or "").strip()

                row_identifiers = {
                    value.casefold()
                    for value in (gene_id, row_accession)
                    if value
                }

                # Do not transfer essentiality results between organisms.
                if row_organism.casefold() != target_organism:
                    continue

                if not identifiers.intersection(row_identifiers):
                    continue

                try:
                    evidence.append(
                        create_essentiality_evidence(
                            gene_id=gene_id,
                            organism=row_organism,
                            essentiality_status=(
                                row["essentiality_status"].strip()
                            ),
                            source=row["source"].strip(),
                            confidence=row["confidence"].strip(),
                            description=row["description"].strip(),
                        )
                    )
                except (ValueError, AttributeError):
                    # Ignore malformed records; never fabricate evidence.
                    continue

    except OSError as exc:
        return {
            "evidence": [],
            "status": "lookup_failed",
            "message": f"Could not read essentiality dataset: {exc}",
        }

    if not evidence:
        return {
            "evidence": [],
            "status": "no_matching_evidence",
            "message": (
                "No matching essentiality evidence was found for this "
                "identifier and organism. This does not establish "
                "that the protein is non-essential."
            ),
        }

    return {
        "evidence": evidence,
        "status": "available",
        "message": f"Loaded {len(evidence)} matching essentiality record(s).",
    }
