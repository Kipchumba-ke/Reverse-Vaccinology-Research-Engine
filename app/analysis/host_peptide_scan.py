"""Scan short peptide windows for matches in a host proteome.

A whole-protein BLASTP search can report no host similarity for a protein
that still carries a short stretch identical to a host protein. This module
searches peptide windows against the same host database using BLAST's
short-query settings.

The scan is off by default (set HOST_PEPTIDE_SCAN=1 to enable it). It
reports matches; it does not establish that a peptide is safe. Absence of
a match only means none was found in the supplied database.
"""

import os

from app.analysis.blast_runner import run_blastp_short
from app.analysis.host_thresholds import (
    HostSimilarityThresholds,
    load_host_similarity_thresholds,
)

METHOD = "BLASTP short-query search (blastp-short, PAM30)"


def is_peptide_scan_enabled() -> bool:
    return os.environ.get("HOST_PEPTIDE_SCAN", "").strip().lower() in {
        "1", "true", "yes", "on",
    }


def select_peptides_for_scan(
    peptides: list[dict],
    max_queries: int,
) -> list[dict]:
    """Choose the peptide windows to search.

    Windows inside predicted antigenic regions come first, then windows
    with a higher mean antigenic propensity. Windows that overlap a
    transmembrane candidate are searched last.
    """
    if max_queries <= 0:
        raise ValueError("max_queries must be greater than zero.")

    def priority(peptide: dict):
        return (
            not peptide.get("overlaps_antigenic_region", False),
            bool(peptide.get("overlaps_transmembrane", False)),
            -peptide.get("mean_antigenic_propensity", 0.0),
            peptide["start"],
        )

    return sorted(peptides, key=priority)[:max_queries]


def peptide_query_id(peptide: dict) -> str:
    return f"pep_{peptide['start']}_{peptide['end']}"


def build_peptide_fasta(peptides: list[dict]) -> str:
    return "".join(
        f">{peptide_query_id(peptide)}\n{peptide['sequence']}\n"
        for peptide in peptides
    )


def parse_peptide_hits(
    output: str,
    peptides: list[dict],
    thresholds: HostSimilarityThresholds,
) -> list[dict]:
    """Turn tabular short-query output into peptide-match records.

    Only alignments with at least thresholds.peptide_min_match identical
    residues are kept. Identical residues are counted from percent identity
    and alignment length, so they need not be contiguous unless
    exact_match is true.
    """
    by_id = {peptide_query_id(peptide): peptide for peptide in peptides}
    hits = []

    for line in output.strip().splitlines():
        fields = line.split("\t")

        if len(fields) != 11:
            raise ValueError(
                "Short-peptide BLAST output must have 11 fields."
            )

        query_id, subject_id = fields[0], fields[1]
        peptide = by_id.get(query_id)

        if peptide is None:
            continue

        percent_identity = float(fields[2])
        alignment_length = int(fields[3])
        identical_residues = round(percent_identity * alignment_length / 100)

        if identical_residues < thresholds.peptide_min_match:
            continue

        hits.append({
            "peptide_start": peptide["start"],
            "peptide_end": peptide["end"],
            "peptide_sequence": peptide["sequence"],
            "host_id": subject_id,
            "identical_residues": identical_residues,
            "alignment_length": alignment_length,
            "percent_identity": percent_identity,
            "exact_match": (
                identical_residues == alignment_length
            ),
            "e_value": float(fields[6]),
            "query_range": [int(fields[7]), int(fields[8])],
            "subject_range": [int(fields[9]), int(fields[10])],
        })

    hits.sort(
        key=lambda hit: (
            -hit["identical_residues"],
            hit["peptide_start"],
            hit["host_id"],
        )
    )
    return hits


def scan_peptides_against_host(
    peptides: list[dict],
    database: str,
    thresholds: HostSimilarityThresholds | None = None,
    runner=run_blastp_short,
) -> dict:
    """Search peptide windows against a host database; never raises on
    BLAST failure, so the main analysis is unaffected."""
    if thresholds is None:
        thresholds = load_host_similarity_thresholds()

    base = {
        "method": METHOD,
        "min_identical_residues": thresholds.peptide_min_match,
        "max_peptides": thresholds.peptide_max_queries,
    }

    if not peptides:
        return {
            **base,
            "status": "not_performed",
            "message": "No peptide windows were available to search.",
            "peptides_searched": 0,
            "peptides_with_matches": 0,
            "matches": [],
        }

    selected = select_peptides_for_scan(
        peptides,
        thresholds.peptide_max_queries,
    )

    try:
        output = runner(build_peptide_fasta(selected), database)
        matches = parse_peptide_hits(output, selected, thresholds)
    except (RuntimeError, ValueError) as error:
        return {
            **base,
            "status": "lookup_failed",
            "message": str(error) or "Short-peptide search failed.",
            "peptides_searched": len(selected),
            "peptides_with_matches": 0,
            "matches": [],
        }

    matched = {(m["peptide_start"], m["peptide_end"]) for m in matches}

    return {
        **base,
        "status": "matches_found" if matches else "no_matches",
        "message": (
            f"{len(matched)} of {len(selected)} searched peptide windows "
            "share an alignment with at least "
            f"{thresholds.peptide_min_match} identical residues with a "
            "host protein."
            if matches
            else "No searched peptide window reached "
            f"{thresholds.peptide_min_match} identical residues with a "
            "host protein in the supplied database. This does not show "
            "that the peptides are absent from the host."
        ),
        "peptides_searched": len(selected),
        "peptides_with_matches": len(matched),
        "matches": matches,
    }
