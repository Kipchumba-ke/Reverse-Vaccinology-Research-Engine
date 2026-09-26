from app.models.evidence import Evidence


def interpret_conservation(
    conservation_percentage: float,
) -> Evidence:
    if conservation_percentage >= 80:
        confidence = "high"
        interpretation = (
            "The analyzed sequences show strong conservation."
        )
    elif conservation_percentage >= 50:
        confidence = "medium"
        interpretation = (
            "The analyzed sequences show moderate conservation."
        )
    else:
        confidence = "low"
        interpretation = (
            "The analyzed sequences show limited conservation."
        )

    finding = (
        f"Fully conserved alignment columns: "
        f"{conservation_percentage:.1f}%"
    )

    return Evidence(
        category="conservation",
        finding=finding,
        interpretation=interpretation,
        confidence=confidence,
    )

def interpret_hydrophobicity(
    gravy: float,
) -> Evidence:
    if gravy >= 0.5:
        confidence = "high"
        interpretation = (
            "The sequence has relatively high overall hydrophobicity."
        )
    elif gravy >= 0:
        confidence = "medium"
        interpretation = (
            "The sequence has mixed but slightly hydrophobic character."
        )
    else:
        confidence = "medium"
        interpretation = (
            "The sequence has relatively hydrophilic overall character."
        )

    finding = f"GRAVY score: {gravy:.2f}"

    return Evidence(
        category="hydrophobicity",
        finding=finding,
        interpretation=interpretation,
        confidence=confidence,
    )

def interpret_transmembrane_candidates(
    candidates: list[dict],
) -> Evidence:
    count = len(candidates)

    if count == 0:
        confidence = "medium"
        interpretation = (
            "No transmembrane candidates were identified "
            "by the current sequence-based heuristic."
        )
    elif count == 1:
        confidence = "medium"
        interpretation = (
            "One region is consistent with a possible "
            "transmembrane segment."
        )
    else:
        confidence = "medium"
        interpretation = (
            f"{count} regions are consistent with possible "
            "transmembrane segments."
        )

    finding = f"Transmembrane candidates: {count}"

    return Evidence(
        category="membrane_topology",
        finding=finding,
        interpretation=interpretation,
        confidence=confidence,
    )

def interpret_conserved_regions(
    regions: list[dict],
) -> Evidence:
    count = len(regions)

    if count == 0:
        confidence = "low"
        interpretation = (
            "No conserved regions meeting the selected "
            "minimum length were identified."
        )
    else:
        confidence = "medium"
        interpretation = (
            f"{count} conserved region(s) were identified "
            "using the supplied alignment."
        )

    finding = f"Conserved regions identified: {count}"

    return Evidence(
        category="conserved_regions",
        finding=finding,
        interpretation=interpretation,
        confidence=confidence,
    ) 

def interpret_host_similarity(
    evidence: list[dict],
) -> Evidence:
    """
    Interpret supplied host-similarity evidence.

    This function does not establish safety.
    It summarizes the supplied similarity results.
    """

    if not evidence:
        return Evidence(
            category="host_similarity",
            finding="No host-similarity evidence supplied.",
            interpretation=(
                "Host-similarity assessment is unavailable "
                "for the current candidate."
            ),
            confidence="low",
        )

    strongest_match = max(
        evidence,
        key=lambda item: (
            item["query_coverage_percentage"],
            item["subject_coverage_percentage"],
            item["identity_percentage"],
            -item["e_value"],
        ),
    )

    identity = strongest_match["identity_percentage"]
    e_value = strongest_match["e_value"]
    query_coverage = strongest_match["query_coverage_percentage"]
    subject_coverage = strongest_match["subject_coverage_percentage"]

    if identity >= 50 and e_value <= 1e-5 and query_coverage >= 70 and subject_coverage >= 70:
        interpretation = (
            "The supplied results include a relatively strong "
            "sequence-similarity match to a host protein with broad "
            "query and subject coverage. This warrants further "
            "investigation. Sequence similarity alone does not "
            "establish biological safety."
        )
        confidence = "high"
    elif (identity >= 50 and e_value <= 1e-5 and (query_coverage < 70 or subject_coverage < 70)):
        interpretation = (
            "The supplied results include high sequence identity "
            "and a strong E-value, but the aligned region does not "
            "cover both sequences broadly. This may represent a "
            "local or partial similarity and warrants further "
            "investigation."
        )
        confidence = "medium"
    elif identity >= 25:
        interpretation = (
            "The supplied results include moderate sequence "
            "similarity to a host protein. The result should be "
            "interpreted alongside alignment coverage and other "
            "biological evidence."
        )
        confidence = "medium"
    else:
        interpretation = (
            "The supplied results show relatively low sequence "
            "similarity to the referenced host proteins. "
            "This does not independently establish safety."
        )
        confidence = "medium"

    finding = (
        f"Strongest reported host match: "
        f"{identity:.1f}% identity, "
        f"query coverage={query_coverage:.1f}%, "
        f"subject coverage={subject_coverage:.1f}%, "
        f"E-value={e_value:g}"
    )

    return Evidence(
        category="host_similarity",
        finding=finding,
        interpretation=interpretation,
        confidence=confidence,
    )

def interpret_localization(
    evidence: list[dict],
) -> Evidence:
    if not evidence:
        return Evidence(
            category="localization",
            finding="No localization evidence supplied.",
            interpretation=(
                "Localization assessment is unavailable "
                "for the current candidate."
            ),
            confidence="low",
        )

    strongest_evidence = max(
        evidence,
        key=lambda item: {
            "low": 1,
            "medium": 2,
            "high": 3,
        }.get(item["confidence"], 0),
    )

    location = strongest_evidence["location"]
    confidence = strongest_evidence["confidence"]
    source = strongest_evidence["source"]
    description = strongest_evidence["description"]

    interpretation = (
        f"The supplied evidence reports "
        f"{location.replace('_', ' ')} localization with "
        f"{confidence} confidence. "
        f"{description}"
    )

    finding = (
        f"Reported localization: "
        f"{location}; source={source}"
    )

    return Evidence(
        category="localization",
        finding=finding,
        interpretation=interpretation,
        confidence=confidence,
    )

def interpret_essentiality(
    evidence: list[dict],
) -> Evidence:
    if not evidence:
        return Evidence(
            category="essentiality",
            finding="No essentiality evidence supplied.",
            interpretation=(
                "Essentiality assessment is unavailable "
                "for the current candidate."
            ),
            confidence="low",
        )

    strongest_evidence = max(
        evidence,
        key=lambda item: {
            "low": 1,
            "medium": 2,
            "high": 3,
        }.get(item["confidence"], 0),
    )

    status = strongest_evidence["essentiality_status"]
    confidence = strongest_evidence["confidence"]
    source = strongest_evidence["source"]
    description = strongest_evidence["description"]

    interpretation = (
        f"The supplied evidence reports the protein as "
        f"{status.replace('_', ' ')} with {confidence} confidence. "
        f"{description}"
    )

    finding = (
        f"Reported essentiality: "
        f"{status}; source={source}"
    )

    return Evidence(
        category="essentiality",
        finding=finding,
        interpretation=interpretation,
        confidence=confidence,
    )


def create_uniprot_annotation_evidence(annotation):
    return Evidence(
        category="uniprot_annotation",
        finding=annotation["protein_name"],
        interpretation=f"UniProt annotation for accession {annotation['accession']}.",
        confidence="high",
    )
