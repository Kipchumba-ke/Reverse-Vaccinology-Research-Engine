from app.analysis.blast import run_blast_analysis
from app.integrations.msa import run_msa
from app.integrations.uniprot import fetch_protein_annotation
from app.analysis.localization import create_localization_evidence


def run_integrations(
    sequence,
    accession,
    blast_database,
    msa_sequences,
):
    uniprot = fetch_protein_annotation(accession)

    blast = run_blast_analysis(
        sequence,
        database=blast_database,
        source="BLAST",
        confidence="medium",
        description="BLAST host-similarity analysis.",
    )

    msa = run_msa(msa_sequences)

    return {
        "uniprot": uniprot,
        "blast": blast,
        "msa": msa,
    }


def convert_uniprot_localizations(annotation):
    """Convert external localization annotations into evidence."""
    source = annotation.get("source", "UniProt")
    evidence_records = []

    for item in annotation.get("localization_annotations", []):
        location = item.get("location")
        if not location:
            continue

        evidence_codes = item.get("evidence_codes", [])
        evidence_text = (
            ", ".join(evidence_codes)
            if evidence_codes
            else "No evidence codes supplied"
        )

        description = (
            f"Location reported by {source}. "
            f"Evidence codes: {evidence_text}. "
            "Confidence has not been independently assessed."
        )

        evidence_records.append(
            create_localization_evidence(
                location=location,
                source=source,
                confidence="low",
                description=description,
            )
        )

    return evidence_records
