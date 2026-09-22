from app.models.analysis_result import ProteinAnalysisResult
from app.analysis.interpretation import (
    interpret_conservation,
    interpret_conserved_regions,
    interpret_hydrophobicity,
    interpret_transmembrane_candidates,
    interpret_host_similarity,
    interpret_localization,
    interpret_essentiality,
)
from app.analysis.candidate_assessment import assess_candidate


def generate_protein_report(
    result: ProteinAnalysisResult,
    conservation_summary: dict | None = None,
    conserved_regions: list[dict] | None = None,
) -> dict:
    """
    Generate an explainable report from analysis results.

    Conservation information is optional because it may come
    from a separate multiple-sequence-alignment analysis.
    """

    if conserved_regions is None:
        conserved_regions = []

    interpretations = [
        interpret_hydrophobicity(result.gravy),
        interpret_transmembrane_candidates(
            result.transmembrane_candidates
        ),
        interpret_conserved_regions(conserved_regions),
        interpret_localization(
            [
                evidence.to_dict()
                for evidence in result.localization_evidence
            ]
        ),
        interpret_essentiality(
            [
                evidence.to_dict()
                for evidence in result.essentiality_evidence
            ]
        ),
        interpret_host_similarity(
            [
                evidence.to_dict()
                for evidence in result.host_similarity_evidence
            ]
        ),
    ]

    if conservation_summary is not None:
        interpretations.append(
            interpret_conservation(
                conservation_summary["conservation_percentage"]
            )
        )
    candidate_assessment = assess_candidate(
        result=result,
        conservation_summary=conservation_summary,
        conserved_regions=conserved_regions,
    )
    

    return {
        "metadata": {
            "report_type": "reverse_vaccinology",
            "report_version": "1.0",
            "analysis_pipeline": "protein_sequence_analysis",
        },
        "protein": {
            "id": result.protein_id,
            "sequence": result.sequence,
            "length": result.length,
            "molecular_weight": result.molecular_weight,
            "gravy": result.gravy,
            "isoelectric_point": result.isoelectric_point,
        },
        "measurements": {
            "composition": result.composition,
            "charge_and_hydrophobicity": (
                result.charge_and_hydrophobicity
            ),
            "hydropathy_profile": result.hydropathy_profile,
            "hydrophobic_regions": result.hydrophobic_regions,
            "transmembrane_candidates": (
                result.transmembrane_candidates
            ),
        },
        "conservation": {
            "summary": conservation_summary,
            "regions": conserved_regions,
        },
        "evidence": {
            "localization": [
                evidence.to_dict()
                for evidence in result.localization_evidence
            ],
            "essentiality": [
                evidence.to_dict()
                for evidence in result.essentiality_evidence
            ],
            "host_similarity": [
                evidence.to_dict()
                for evidence in result.host_similarity_evidence
            ],
        },
        "interpretations": [
            interpretation.to_dict()
            for interpretation in interpretations
        ],
        "candidate_assessment": candidate_assessment.to_dict(),
        "limitations": [
            (
                "Hydrophobic regions and transmembrane candidates "
                "are sequence-based heuristics."
            ),
            (
                "Localization evidence must come from an external "
                "prediction tool, database, or experiment."
            ),
            (
                "Essentiality evidence is recorded from supplied "
                "sources and is not independently predicted."
            ),
            (
                "Conservation depends on the supplied alignment "
                "and conservation definition."
            ),
            (
                "Host-similarity evidence is based on supplied search results "
                "and does not independently establish absence of host similarity "
                "or vaccine safety."
            ),
        ],
        
    }