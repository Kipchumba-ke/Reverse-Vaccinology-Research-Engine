from app.analysis.pipeline import analyze_protein
from app.reporting.report import generate_protein_report


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