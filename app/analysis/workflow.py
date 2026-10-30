import os

from app.analysis.conservation import (
    calculate_conservation_summary,
    calculate_similarity_summary,
    calculate_conserved_columns,
    find_conserved_regions,
)
from app.analysis.msa import align_sequences
from app.models.workflow_result import AnalysisWorkflowResult
from app.input.fasta import parse_fasta_records
from app.analysis.pipeline import analyze_protein


def _get_alignment_scoring() -> str:
    """Scoring used by the built-in aligner (ALIGNMENT_SCORING).

    Defaults to "blosum62". Set ALIGNMENT_SCORING=identity to score matches
    and mismatches only.
    """
    scoring = os.environ.get("ALIGNMENT_SCORING", "blosum62").strip().lower()

    if scoring not in {"identity", "blosum62"}:
        raise ValueError(
            "ALIGNMENT_SCORING must be 'identity' or 'blosum62'."
        )

    return scoring


def analyze_fasta_records(records: list[dict], localization_evidence: dict[str, list] | None = None, essentiality_evidence: dict[str, list] | None = None, host_similarity_evidence: dict[str, list] | None = None,) -> AnalysisWorkflowResult:
    if not records:
        raise ValueError(
            "At least one FASTA record is required."
        )
    if localization_evidence is None:
        localization_evidence = {}

    if essentiality_evidence is None:
        essentiality_evidence = {}

    if host_similarity_evidence is None:
        host_similarity_evidence = {}
    for record in records:
        if "id" not in record or "sequence" not in record:
            raise ValueError(
                "FASTA record must contain id and sequence."
            )

    sequences = [record["sequence"] for record in records]

    protein_analyses = [
        analyze_protein(
            record["sequence"],
            localization_evidence=localization_evidence.get(
                record["id"],
                [],
            ),
            essentiality_evidence=essentiality_evidence.get(
                record["id"],
                [],
            ),
            host_similarity_evidence=host_similarity_evidence.get(
                record["id"],
                [],
            ),
            protein_id=record["id"],
            protein_name=record.get("description"),
            organism=record.get("organism"),
            accession=record.get("accession"),
        )
        for record in records
    ]
    alignment = align_sequences(sequences, scoring=_get_alignment_scoring())
    conservation_columns = calculate_conserved_columns(alignment)
    conservation = calculate_conservation_summary(alignment)
    conservation_similarity = calculate_similarity_summary(alignment)
    conserved_regions = find_conserved_regions(
        conservation_columns
    )
    for analysis in protein_analyses:
        analysis.conservation_columns = conservation_columns
        analysis.conservation_summary = conservation
        analysis.conservation_similarity = conservation_similarity

    return AnalysisWorkflowResult(
        records=records,
        protein_analyses=protein_analyses,
        alignment=alignment,
        conservation=conservation,
        conserved_regions=conserved_regions,
        
    )

def analyze_fasta(fasta_text: str, localization_evidence: dict[str, list] | None = None, essentiality_evidence: dict[str, list] | None = None, host_similarity_evidence: dict[str, list] | None = None,) -> AnalysisWorkflowResult:
    records = parse_fasta_records(fasta_text)

    return analyze_fasta_records(
        records,
        localization_evidence=localization_evidence,
        essentiality_evidence=essentiality_evidence,
        host_similarity_evidence=host_similarity_evidence
        )