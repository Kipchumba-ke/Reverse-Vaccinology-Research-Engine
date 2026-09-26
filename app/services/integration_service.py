from app.analysis.blast import run_blast_analysis
from app.integrations.msa import run_msa
from app.integrations.uniprot import fetch_protein_annotation


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