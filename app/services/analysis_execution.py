
from app.services.analysis_service import (
    analyze_sequence,
    analyze_fasta_records,
)
from app.input.fasta import parse_fasta_records


def execute_analysis(analysis, repository=None):
    analysis.status = "running"

    if repository is not None:
        repository.update(analysis)

    try:
        if analysis.sequence.lstrip().startswith(">"):
            records = parse_fasta_records(analysis.sequence)
            result = analyze_fasta_records(records)
        else:
            result = analyze_sequence(
                analysis.sequence,
                protein_id=analysis.protein_id,
                protein_name=analysis.protein_name,
                organism=analysis.organism,
                accession=analysis.accession,
            )
    except Exception:
        analysis.status = "failed"

        if repository is not None:
            repository.update(analysis)

        raise

    analysis.report = result
    analysis.status = "completed"

    if repository is not None:
        repository.update(analysis)

    return result
