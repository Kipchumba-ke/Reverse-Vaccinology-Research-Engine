
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

            if len(records) == 1:
                result = analyze_fasta_records(
                    records,
                    epath_gene_id=analysis.epath_gene_id,
                    epath_ko_id=analysis.epath_ko_id,
                    organism=analysis.organism,
                    host_reference=analysis.host_reference,
                )
            else:
                result = analyze_fasta_records(
                    records,
                    epath_gene_id=analysis.epath_gene_id,
                    epath_ko_id=analysis.epath_ko_id,
                    organism=analysis.organism,
                    host_reference=analysis.host_reference,
                )
        else:
            result = analyze_sequence(
                analysis.sequence,
                protein_id=analysis.protein_id,
                protein_name=analysis.protein_name,
                organism=analysis.organism,
                accession=analysis.accession,
                epath_gene_id=analysis.epath_gene_id,
                epath_ko_id=analysis.epath_ko_id,
                host_reference=analysis.host_reference,
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
