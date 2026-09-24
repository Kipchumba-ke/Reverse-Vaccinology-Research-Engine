from app.analysis.pipeline import analyze_protein
from app.reporting.report import generate_protein_report
from app.analysis.workflow import analyze_fasta_records as run_fasta_workflow
from app.models.analysis import Analysis
from app.utils.validation import validate_protein_sequence


def analyze_sequence(
    sequence: str,
    protein_id: str | None = None,
    protein_name: str | None = None,
    organism: str | None = None,
    accession: str | None = None,
):
    result = analyze_protein(
        sequence,
        protein_id=protein_id,
        protein_name=protein_name,
        organism=organism,
        accession=accession,
    )

    return generate_protein_report(result)


def analyze_fasta_records(records: list[dict]):
    if len(records) == 1:
        record = records[0]

        return analyze_sequence(
            record["sequence"],
            protein_id=record.get("id"),
            protein_name=record.get("description"),
            organism=record.get("organism"),
            accession=record.get("accession"),
        )

    return run_fasta_workflow(records).to_dict()


def persist_analysis(analysis, repository):
    return repository.save(analysis)


def create_analysis(
    sequence: str,
    protein_id: str | None = None,
    protein_name: str | None = None,
    organism: str | None = None,
    accession: str | None = None,
):
    cleaned_sequence = validate_protein_sequence(sequence)
    return Analysis(
        protein_id=protein_id,
        protein_name=protein_name,
        organism=organism,
        accession=accession,
        sequence=cleaned_sequence,
    )


def run_analysis(
    sequence: str,
    repository,
    protein_id: str | None = None,
    protein_name: str | None = None,
    organism: str | None = None,
    accession: str | None = None,
):
    analysis = create_analysis(
        sequence,
        protein_id=protein_id,
        protein_name=protein_name,
        organism=organism,
        accession=accession,
    )

    persist_analysis(analysis, repository)

    return analyze_sequence(
        analysis.sequence,
        protein_id=analysis.protein_id,
        protein_name=analysis.protein_name,
        organism=analysis.organism,
        accession=analysis.accession,
    )
