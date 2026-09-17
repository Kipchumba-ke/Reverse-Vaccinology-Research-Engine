from app.models.host_similarity import HostSimilarityEvidence


VALID_CONFIDENCE_LEVELS = {
    "low",
    "medium",
    "high",
}


def create_host_similarity_evidence(
    target_id: str,
    host_id: str,
    similarity_method: str,
    identity_percentage: float,
    alignment_length: int,
    e_value: float,
    source: str,
    confidence: str,
    description: str,
) -> HostSimilarityEvidence:

    if not target_id.strip():
        raise ValueError("Target ID cannot be empty.")

    if not host_id.strip():
        raise ValueError("Host ID cannot be empty.")

    if not similarity_method.strip():
        raise ValueError(
            "Similarity method cannot be empty."
        )

    if not 0 <= identity_percentage <= 100:
        raise ValueError(
            "Identity percentage must be between 0 and 100."
        )

    if alignment_length <= 0:
        raise ValueError(
            "Alignment length must be greater than zero."
        )

    if e_value < 0:
        raise ValueError(
            "E-value cannot be negative."
        )

    if not source.strip():
        raise ValueError(
            "Host similarity evidence source cannot be empty."
        )

    if confidence not in VALID_CONFIDENCE_LEVELS:
        raise ValueError(
            f"Unsupported confidence level: {confidence}"
        )

    if not description.strip():
        raise ValueError(
            "Host similarity description cannot be empty."
        )

    return HostSimilarityEvidence(
        target_id=target_id,
        host_id=host_id,
        similarity_method=similarity_method,
        identity_percentage=identity_percentage,
        alignment_length=alignment_length,
        e_value=e_value,
        source=source,
        confidence=confidence,
        description=description,
    )