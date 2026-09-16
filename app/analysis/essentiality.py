from app.models.essentiality import EssentialityEvidence


VALID_ESSENTIALITY_STATUSES = {
    "essential",
    "non-essential",
    "conditionally_essential",
    "unknown",
}

VALID_CONFIDENCE_LEVELS = {
    "low",
    "medium",
    "high",
}


def create_essentiality_evidence(
    gene_id: str,
    organism: str,
    essentiality_status: str,
    source: str,
    confidence: str,
    description: str,
) -> EssentialityEvidence:
    """
    Create a validated essentiality evidence record.

    This function records external evidence.
    It does not independently predict essentiality.
    """

    if not gene_id.strip():
        raise ValueError("Gene ID cannot be empty.")

    if not organism.strip():
        raise ValueError("Organism cannot be empty.")

    if essentiality_status not in VALID_ESSENTIALITY_STATUSES:
        raise ValueError(
            f"Unsupported essentiality status: {essentiality_status}"
        )

    if not source.strip():
        raise ValueError("Essentiality evidence source cannot be empty.")

    if confidence not in VALID_CONFIDENCE_LEVELS:
        raise ValueError(
            f"Unsupported confidence level: {confidence}"
        )

    if not description.strip():
        raise ValueError(
            "Essentiality evidence description cannot be empty."
        )

    return EssentialityEvidence(
        gene_id=gene_id,
        organism=organism,
        essentiality_status=essentiality_status,
        source=source,
        confidence=confidence,
        description=description,
    )