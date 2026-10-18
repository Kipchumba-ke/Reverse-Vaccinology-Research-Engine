from app.models.localization import LocalizationEvidence


VALID_LOCATIONS = {
    "cytoplasm",
    "inner_membrane",
    "periplasm",
    "outer_membrane",
    "extracellular",
    "unknown",
}

VALID_CONFIDENCE_LEVELS = {
    "low",
    "medium",
    "high",
}


def create_localization_evidence(
    location: str,
    source: str,
    confidence: str,
    description: str,
) -> LocalizationEvidence:
    """
    Create a validated localization evidence record.

    This function does not predict localization.
    It represents evidence obtained from an external
    prediction tool, database, or experimental source.
    """

    if not isinstance(location, str) or not location.strip():
        raise ValueError("Localization cannot be empty.")

    EXTERNAL_ANNOTATION_SOURCES = {
        "UniProt",
        "NCBI Protein",
    }
    if (
        location not in VALID_LOCATIONS
        and source not in EXTERNAL_ANNOTATION_SOURCES
    ):
        raise ValueError(f"Unsupported localization: {location}")

    if not isinstance(source, str) or not source.strip():
        raise ValueError("Localization evidence source cannot be empty.")

    if confidence not in VALID_CONFIDENCE_LEVELS:
        raise ValueError("Unsupported confidence level: " + str(confidence))

    if not isinstance(description, str) or not description.strip():
        raise ValueError("Localization evidence description cannot be empty.")

    return LocalizationEvidence(
        location=location,
        source=source,
        confidence=confidence,
        description=description,
    )