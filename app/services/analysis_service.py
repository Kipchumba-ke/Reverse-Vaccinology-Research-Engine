from app.analysis.pipeline import analyze_protein
from app.reporting.report import generate_protein_report
from app.analysis.workflow import analyze_fasta_records as run_fasta_workflow


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
