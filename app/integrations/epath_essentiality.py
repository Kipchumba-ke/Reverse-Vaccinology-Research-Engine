"""Look up organism-specific essentiality evidence from ePath."""

import os
import sqlite3
from pathlib import Path

from app.models.essentiality import EssentialityEvidence


DEFAULT_DB_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "reference"
    / "essentiality"
    / "epath.sqlite3"
)

ESSENTIALITY_SYMBOLS = {
    "*": "essential",
    "x": "non-essential",
}


def fetch_epath_essentiality_evidence(
    organism: str | None,
    gene_id: str | None = None,
    ko_id: str | None = None,
    database_path: str | None = None,
) -> dict:
    """
    Fetch experimentally classified ePath essentiality evidence.

    Matching requires an exact organism name or abbreviation and either
    a gene identifier present in epath_gene or a KO identifier.

    Unclassified symbols are not interpreted as evidence that a gene
    is essential or non-essential.
    """
    empty_result = {"evidence": [], "status": "", "message": ""}

    if not organism or not organism.strip():
        return {
            **empty_result,
            "status": "organism_required",
            "message": "An organism name or abbreviation is required.",
        }

    if not gene_id and not ko_id:
        return {
            **empty_result,
            "status": "identifier_required",
            "message": (
                "A verified ePath gene identifier or KO identifier "
                "is required. Protein sequence identifiers alone "
                "are not assumed to be ePath identifiers."
            ),
        }

    path = Path(
        database_path
        or os.environ.get("ESSENTIALITY_EPATH_DB_PATH")
        or DEFAULT_DB_PATH
    )

    if not path.is_file():
        return {
            **empty_result,
            "status": "not_configured",
            "message": f"ePath database not found: {path}",
        }

    organism_input = organism.strip()
    gene_id = gene_id.strip() if gene_id else None
    ko_id = ko_id.strip() if ko_id else None

    try:
        with sqlite3.connect(str(path)) as connection:
            connection.row_factory = sqlite3.Row

            # Resolve only exact organism names or abbreviations.
            organism_rows = connection.execute(
                """
                SELECT organism_abbreviation, organism
                FROM epath_experimental_records
                WHERE LOWER(organism_abbreviation) = LOWER(?)
                   OR LOWER(organism) = LOWER(?)

                UNION

                SELECT organism_abbreviation, organism
                FROM epath_gene
                WHERE LOWER(organism_abbreviation) = LOWER(?)
                   OR LOWER(organism) = LOWER(?)
                LIMIT 2
                """,
                (
                    organism_input,
                    organism_input,
                    organism_input,
                    organism_input,
                ),
            ).fetchall()

            # A name resolving ambiguously must not be guessed.
            abbreviations = {
                row["organism_abbreviation"] for row in organism_rows
            }

            if len(abbreviations) != 1:
                return {
                    **empty_result,
                    "status": (
                        "organism_not_found"
                        if not abbreviations
                        else "organism_ambiguous"
                    ),
                    "message": (
                        "The organism did not match an ePath reference."
                        if not abbreviations
                        else (
                            "The organism matched multiple ePath "
                            "references. Supply its exact abbreviation."
                        )
                    ),
                }

            abbreviation = next(iter(abbreviations))

            # If a gene ID is supplied, require an exact match within
            # the resolved organism before accepting its KO mapping.
            if gene_id:
                gene_rows = connection.execute(
                    """
                    SELECT DISTINCT ko_id
                    FROM epath_gene
                    WHERE organism_abbreviation = ?
                      AND LOWER(gene_id) = LOWER(?)
                      AND ko_id IS NOT NULL
                      AND TRIM(ko_id) != ''
                    """,
                    (abbreviation, gene_id),
                ).fetchall()

                mapped_kos = {row["ko_id"] for row in gene_rows}

                if not mapped_kos:
                    return {
                        **empty_result,
                        "status": "no_matching_evidence",
                        "message": (
                            "No ePath gene-to-KO mapping was found for "
                            "this identifier and organism."
                        ),
                    }

                if ko_id and ko_id not in mapped_kos:
                    return {
                        **empty_result,
                        "status": "identifier_conflict",
                        "message": (
                            "The supplied gene and KO identifiers do not "
                            "match the same ePath gene mapping."
                        ),
                    }

                # Do not silently choose between multiple KO mappings.
                if len(mapped_kos) != 1:
                    return {
                        **empty_result,
                        "status": "ambiguous_gene_mapping",
                        "message": (
                            "The gene identifier maps to multiple KO "
                            "identifiers. Supply a verified KO mapping."
                        ),
                    }

                ko_id = next(iter(mapped_kos))

            row = connection.execute(
                """
                SELECT symbol
                FROM epath_ko_essentiality
                WHERE organism_abbreviation = ?
                  AND ko_id = ?
                """,
                (abbreviation, ko_id),
            ).fetchone()

            if row is None:
                return {
                    **empty_result,
                    "status": "no_matching_evidence",
                    "message": (
                        "No ePath essentiality classification was found "
                        "for this KO and organism."
                    ),
                }

            symbol = row["symbol"]

            if symbol not in ESSENTIALITY_SYMBOLS:
                return {
                    **empty_result,
                    "status": "unclassified",
                    "message": (
                        f"ePath returned symbol {symbol!r}. This record "
                        "does not establish essentiality or "
                        "non-essentiality."
                    ),
                }

            status = ESSENTIALITY_SYMBOLS[symbol]

            organism_name = next(
                (
                    row["organism"]
                    for row in organism_rows
                    if row["organism_abbreviation"] == abbreviation
                    and row["organism"]
                ),
                organism_input,
            )

            identifier_label = gene_id or f"KO:{ko_id}"
            evidence = EssentialityEvidence(
                gene_id=identifier_label,
                organism=organism_name,
                essentiality_status=status,
                source="ePath",
                confidence="high",
                description=(
                    f"ePath classifies KO {ko_id} for "
                    f"{organism_name} with symbol {symbol!r}, "
                    f"indicating {status}. This is organism-specific "
                    "reference evidence, not proof of essentiality "
                    "under every biological condition."
                ),
            )

            return {
                "evidence": [evidence],
                "status": "available",
                "message": (
                    f"Retrieved ePath {status} classification for "
                    f"KO {ko_id} in {organism_name}."
                ),
            }

    except (sqlite3.Error, OSError) as exc:
        return {
            **empty_result,
            "status": "lookup_failed",
            "message": f"ePath lookup failed: {exc}",
        }
