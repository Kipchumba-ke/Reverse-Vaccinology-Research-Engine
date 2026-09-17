from app.models.analysis_result import ProteinAnalysisResult
from app.models.candidate_assessment import CandidateAssessment


def assess_candidate(
    result: ProteinAnalysisResult,
    conservation_summary: dict | None = None,
    conserved_regions: list[dict] | None = None,
) -> CandidateAssessment:
    """
    Create a transparent evidence summary for a protein candidate.

    This function does not establish vaccine safety, antigenicity,
    or final vaccine candidacy.
    """

    if conserved_regions is None:
        conserved_regions = []

    supporting_evidence = []
    concerns = []
    missing_evidence = []

    # Localization evidence
    if result.localization_evidence:
        supporting_evidence.append(
            "Localization evidence has been supplied."
        )
    else:
        missing_evidence.append(
            "Localization evidence from a prediction tool, database, "
            "or experiment."
        )

    # Essentiality evidence
    if result.essentiality_evidence:
        supporting_evidence.append(
            "Essentiality evidence has been supplied."
        )
    else:
        missing_evidence.append(
            "Essentiality evidence from an appropriate external source."
        )

    # Host similarity evidence
    if result.host_similarity_evidence:
        concerns.append(
            "Host-similarity evidence requires biological and "
            "alignment-level review."
        )
    else:
        missing_evidence.append(
            "Host-protein similarity analysis."
        )

    # Conservation
    if conservation_summary is not None:
        conservation_percentage = (
            conservation_summary["conservation_percentage"]
        )

        if conservation_percentage >= 50:
            supporting_evidence.append(
                "The supplied alignment contains conserved positions."
            )
        else:
            concerns.append(
                "The supplied alignment shows limited exact conservation."
            )
    else:
        missing_evidence.append(
            "Multiple-sequence alignment and conservation analysis."
        )

    # Conserved regions
    if conserved_regions:
        supporting_evidence.append(
            "One or more conserved regions were detected."
        )
    else:
        concerns.append(
            "No conserved regions were supplied or detected."
        )

    # Hydrophobicity and transmembrane candidates
    if result.transmembrane_candidates:
        concerns.append(
            "Possible transmembrane segments were detected using "
            "sequence-based heuristics."
        )

    # Status
    if missing_evidence:
        status = "requires_further_review"
    elif concerns:
        status = "requires_further_review"
    else:
        status = "evidence_compiled"

    return CandidateAssessment(
        status=status,
        supporting_evidence=supporting_evidence,
        concerns=concerns,
        missing_evidence=missing_evidence,
    )