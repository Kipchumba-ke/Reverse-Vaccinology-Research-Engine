from app.analysis.conservation import calculate_conservation_summary
from app.analysis.msa import align_sequences
from app.models.workflow_result import AnalysisWorkflowResult
from app.input.fasta import parse_fasta_records


def analyze_fasta_records(records: list[dict]) -> AnalysisWorkflowResult:
    if not records:
        raise ValueError(
            "At least one FASTA record is required."
        )
    for record in records:
        if "id" not in record or "sequence" not in record:
            raise ValueError(
                "FASTA record must contain id and sequence."
            )       
    sequences = [record["sequence"] for record in records]

    alignment = align_sequences(sequences)
    conservation = calculate_conservation_summary(alignment)

    return AnalysisWorkflowResult(
        records=records,
        alignment=alignment,
        conservation=conservation,
    )

def analyze_fasta(fasta_text: str) -> AnalysisWorkflowResult:
    records = parse_fasta_records(fasta_text)

    return analyze_fasta_records(records)