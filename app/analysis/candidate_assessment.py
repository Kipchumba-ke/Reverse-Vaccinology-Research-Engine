from app.models.analysis_result import ProteinAnalysisResult
from app.models.candidate_assessment import CandidateAssessment
from app.models.evidence_assessment import EvidenceAssessment
from app.models.host_similarity import HostSimilarityEvidence


def _get_conservation_percentage(
    conservation_summary: dict,
) -> float:
    """
    Extract and validate conservation percentage.

    Candidate assessment currently accepts serialized conservation
    summaries represented as dictionaries.
    """

    if "conservation_percentage" not in conservation_summary:
        raise ValueError(
            "Conservation summary must contain "
            "'conservation_percentage'."
        )

    conservation_percentage = (
        conservation_summary["conservation_percentage"]
    )

    if (
        isinstance(conservation_percentage, bool)
        or not isinstance(conservation_percentage, int | float)
    ):
        raise ValueError(
            "Conservation percentage must be numeric."
        )

    if not 0 <= conservation_percentage <= 100:
        raise ValueError(
            "Conservation percentage must be between 0 and 100."
        )

    return float(conservation_percentage)

def _assess_localization_evidence(
    result: ProteinAnalysisResult,
) -> EvidenceAssessment:
    supporting_evidence = []
    concerns = []
    missing_evidence = []

    if not result.localization_evidence:
        missing_evidence.append(
            "Localization evidence from a prediction tool, database, "
            "or experiment."
        )

        return EvidenceAssessment(
            supporting_evidence=supporting_evidence,
            concerns=concerns,
            missing_evidence=missing_evidence,
        )

    supporting_evidence.append(
        "Localization evidence has been supplied."
    )
    locations = {
        evidence.location
        for evidence in result.localization_evidence
        if evidence.location != "unknown"
    }
    if (
        len(result.localization_evidence) > 1
        and len(locations) == 1
    ):
        supporting_evidence.append(
            "Multiple localization predictions agree on the same location."
        )

    if len(locations) > 1:
        concerns.append(
            "Conflicting localization predictions were supplied "
            f"for: {', '.join(sorted(locations))}."
        )

    for evidence in result.localization_evidence:
        if evidence.location == "unknown":
            concerns.append(
                "Localization is unknown "
                f"(confidence={evidence.confidence}, "
                f"source={evidence.source})."
            )
            continue

        supporting_evidence.append(
            f"Predicted localization: {evidence.location}."
        )

        supporting_evidence.append(
            "Predicted localization: "
            f"{evidence.location} "
            f"(confidence={evidence.confidence}, "
            f"source={evidence.source})."
            f"Description: {evidence.description}"
        )

    return EvidenceAssessment(
        supporting_evidence=supporting_evidence,
        concerns=concerns,
        missing_evidence=missing_evidence,
    )

def _assess_essentiality_evidence(
    result: ProteinAnalysisResult,
) -> EvidenceAssessment:
    supporting_evidence = []
    concerns = []
    missing_evidence = []

    if not result.essentiality_evidence:
        missing_evidence.append(
            "Essentiality evidence from an appropriate external source."
        )

        return EvidenceAssessment(
            supporting_evidence=supporting_evidence,
            concerns=concerns,
            missing_evidence=missing_evidence,
        )

    supporting_evidence.append(
        "Essentiality evidence has been supplied."
    )

    statuses = {
        evidence.essentiality_status
        for evidence in result.essentiality_evidence
        if evidence.essentiality_status != "unknown"
    }
    if len(statuses) > 1:
        concerns.append(
            "Conflicting essentiality evidence was supplied for: "
            f"{', '.join(sorted(statuses))}."
        )

    if (
        len(result.essentiality_evidence) > 1
        and len(statuses) == 1
    ):
        supporting_evidence.append(
            "Multiple essentiality records agree on the same status."
        )

    for evidence in result.essentiality_evidence:
        if evidence.essentiality_status == "unknown":
            concerns.append(
                "Essentiality status is unknown "
                f"(gene={evidence.gene_id}, "
                f"organism={evidence.organism}, "
                f"confidence={evidence.confidence}, "
                f"source={evidence.source})."
            )
            continue

        supporting_evidence.append(
            "Essentiality status: "
            f"{evidence.essentiality_status} "
            f"(gene={evidence.gene_id}, "
            f"organism={evidence.organism}, "
            f"confidence={evidence.confidence}, "
            f"source={evidence.source}). "
            f"Description: {evidence.description}"
        )

    return EvidenceAssessment(
        supporting_evidence=supporting_evidence,
        concerns=concerns,
        missing_evidence=missing_evidence,
    )

def _get_highest_identity_host_match(
    evidence: list[HostSimilarityEvidence],
) -> HostSimilarityEvidence:
    return max(
        evidence,
        key=lambda item: (
            item.identity_percentage,
            item.query_coverage_percentage,
            item.subject_coverage_percentage,
            -item.e_value,
        ),
    )

def _get_strongest_host_match(
    evidence: list[HostSimilarityEvidence],
) -> HostSimilarityEvidence:
    return max(
        evidence,
        key=lambda item: (
            item.query_coverage_percentage,
            item.subject_coverage_percentage,
            item.identity_percentage,
            -item.e_value,
        ),
    )

def _interpret_host_similarity(
    evidence,
) -> str:
    if (
        (
            evidence.query_coverage_percentage >= 80
            and evidence.subject_coverage_percentage < 80
        )
        or (
            evidence.query_coverage_percentage < 80
            and evidence.subject_coverage_percentage >= 80
        )
    ):
        return (
            "Asymmetric host-protein similarity coverage "
            "was reported."
        )

    if (
        evidence.identity_percentage >= 70
        and evidence.query_coverage_percentage >= 80
        and evidence.subject_coverage_percentage >= 80
    ):
        return (
            "Broad host-protein similarity was reported "
            "across most of both aligned proteins."
        )

    if (
        evidence.identity_percentage >= 70
        and evidence.query_coverage_percentage < 80
        and evidence.subject_coverage_percentage < 80
    ):
        return (
            "Partial host-protein similarity was reported "
            "within a limited aligned region."
        )

    if (
        evidence.identity_percentage >= 30
        and evidence.identity_percentage < 70
    ):
        return (
            "Moderate host-protein sequence similarity "
            "was reported."
        )

    if evidence.identity_percentage < 30:
        return (
            "Relatively low sequence similarity was reported "
            "against the supplied host protein."
        )

    return "Host-protein similarity was reported."

def _assess_host_similarity_evidence(
    result: ProteinAnalysisResult,
) -> EvidenceAssessment:
    supporting_evidence = []
    concerns = []
    missing_evidence = []

    if result.host_similarity_evidence:
        strongest_host_match = _get_strongest_host_match(
            result.host_similarity_evidence
        )

        highest_identity_match = _get_highest_identity_host_match(
            result.host_similarity_evidence
        )

        concerns.append(
            "Host-similarity evidence requires biological and "
            "alignment-level review."
        )
        concerns.append(
            f"{len(result.host_similarity_evidence)} "
            "host-protein similarity records were supplied."
        )

        concerns.append(
            "Strongest reported host match: "
            f"{strongest_host_match.identity_percentage:.1f}% identity, "
            f"query coverage="
            f"{strongest_host_match.query_coverage_percentage:.1f}%, "
            f"subject coverage="
            f"{strongest_host_match.subject_coverage_percentage:.1f}%, "
            f"E-value={strongest_host_match.e_value:g}."
        )


        concerns.append(
            "Highest-identity host match: "
            f"{highest_identity_match.identity_percentage:.1f}% identity, "
            f"query coverage="
            f"{highest_identity_match.query_coverage_percentage:.1f}%, "
            f"subject coverage="
            f"{highest_identity_match.subject_coverage_percentage:.1f}%, "
            f"E-value={highest_identity_match.e_value:g}."
        )

        concerns.append(
            _interpret_host_similarity(strongest_host_match)
        )

    else:
        missing_evidence.append(
            "Host-protein similarity analysis."
        )

    return EvidenceAssessment(
        supporting_evidence=supporting_evidence,
        concerns=concerns,
        missing_evidence=missing_evidence,
    )

def _assess_conservation_evidence(
    conservation_summary: dict | None,
) -> EvidenceAssessment:
    supporting_evidence = []
    concerns = []
    missing_evidence = []

    if conservation_summary is not None:
        conservation_percentage = (
            _get_conservation_percentage(
                conservation_summary
            )
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

    return EvidenceAssessment(
        supporting_evidence=supporting_evidence,
        concerns=concerns,
        missing_evidence=missing_evidence,
    )

def _assess_conserved_regions(
    conserved_regions: list[dict],
) -> EvidenceAssessment:
    supporting_evidence = []
    concerns = []

    if conserved_regions:
        supporting_evidence.append(
            "One or more conserved regions were detected."
        )
    else:
        concerns.append(
            "No conserved regions were supplied or detected."
        )

    return EvidenceAssessment(
        supporting_evidence=supporting_evidence,
        concerns=concerns,
        missing_evidence=[],
    )

def _assess_transmembrane_candidates(
    result: ProteinAnalysisResult,
) -> EvidenceAssessment:
    concerns = []

    if result.transmembrane_candidates:
        concerns.append(
            "Possible transmembrane segments were detected using "
            "sequence-based heuristics."
        )
    return EvidenceAssessment(
        supporting_evidence=[],
        concerns=concerns,
        missing_evidence=[],
    )

def _merge_evidence_assessment(
    assessment: EvidenceAssessment,
    supporting_evidence: list[str],
    concerns: list[str],
    missing_evidence: list[str],
) -> None:
    supporting_evidence.extend(
        assessment.supporting_evidence
    )
    concerns.extend(
        assessment.concerns
    )
    missing_evidence.extend(
        assessment.missing_evidence
    )

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

    localization = _assess_localization_evidence(result)
    essentiality = _assess_essentiality_evidence(result)
    host_similarity = _assess_host_similarity_evidence(result)
    conservation = _assess_conservation_evidence(
        conservation_summary
    )
    regions = _assess_conserved_regions(conserved_regions)
    transmembrane = _assess_transmembrane_candidates(result)

    for assessment in (
        localization,
        essentiality,
        host_similarity,
        conservation,
        regions,
        transmembrane,
    ):
        _merge_evidence_assessment(
            assessment,
            supporting_evidence,
            concerns,
            missing_evidence,
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

