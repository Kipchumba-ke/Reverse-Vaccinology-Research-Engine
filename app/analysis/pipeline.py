from app.analysis.composition import (
    calculate_amino_acid_composition,
)
from app.analysis.hydrophobicity import (
    calculate_gravy,
    calculate_hydropathy_profile,
    find_hydrophobic_regions,
    merge_hydrophobic_regions,
    summarize_hydrophobic_regions,
    classify_transmembrane_candidates,
)
from app.analysis.properties import (
    calculate_molecular_weight,
    calculate_charge_and_hydrophobicity,
    calculate_isoelectric_point,
)
from app.models.analysis_result import ProteinAnalysisResult
from app.utils.validation import validate_protein_sequence
from app.models.localization import LocalizationEvidence
from app.analysis.epitope import (
    calculate_peptide_properties,
    generate_peptide_windows,
    annotate_transmembrane_overlap,
)
from app.analysis.conservation import (
    calculate_conservation_summary,
    calculate_conserved_columns,
)


def analyze_protein(
    sequence: str,
    ph: float = 7.0,
    hydropathy_window_size: int = 19,
    hydropathy_threshold: float = 1.6,
    tm_min_length: int = 18,
    tm_max_length: int = 25,
    tm_min_hydropathy: float = 1.6,
    peptide_window_size: int = 15,
    localization_evidence: list[LocalizationEvidence] | None = None,
    essentiality_evidence = None,
    host_similarity_evidence = None,
    protein_id: str | None = None,
    protein_name: str | None = None,
    organism: str | None = None,
    accession: str | None = None,
    aligned_sequences: list[str] | None = None,
    conservation_summary: dict | None = None
) -> ProteinAnalysisResult:
    """
    Run the complete protein analysis pipeline.

    The sequence is validated and normalized once,
    then passed to the individual analysis functions.
    """

    cleaned_sequence = validate_protein_sequence(sequence)

    composition = calculate_amino_acid_composition(
        cleaned_sequence
    )

    molecular_weight = calculate_molecular_weight(
        cleaned_sequence
    )

    gravy = calculate_gravy(cleaned_sequence)

    charge_and_hydrophobicity = (
        calculate_charge_and_hydrophobicity(
            cleaned_sequence
        )
    )

    isoelectric_point = calculate_isoelectric_point(
        cleaned_sequence
    )
    if localization_evidence is None:
        localization_evidence = []

    if essentiality_evidence is None:
        essentiality_evidence = []

    if host_similarity_evidence is None:
        host_similarity_evidence = []

    if len(cleaned_sequence) >= hydropathy_window_size:
        hydropathy_profile = calculate_hydropathy_profile(
            cleaned_sequence,
            window_size=hydropathy_window_size,
        )

        hydrophobic_windows = find_hydrophobic_regions(
            cleaned_sequence,
            window_size=hydropathy_window_size,
            threshold=hydropathy_threshold,
        )

        merged_regions = merge_hydrophobic_regions(
            hydrophobic_windows
        )

        hydrophobic_regions = summarize_hydrophobic_regions(
            cleaned_sequence,
            merged_regions,
        )

        transmembrane_candidates = classify_transmembrane_candidates(
            hydrophobic_regions,
            min_length=tm_min_length,
            max_length=tm_max_length,
            min_hydropathy=tm_min_hydropathy,
        )
    else:
        hydropathy_profile = []
        hydrophobic_regions = []
        transmembrane_candidates = []

    if len(cleaned_sequence) >= peptide_window_size:
        peptide_candidates = generate_peptide_windows(
            cleaned_sequence,
            peptide_window_size,
        )

        peptide_candidates = [
            {
                **peptide,
                **{
                    key: value
                    for key, value in calculate_peptide_properties(
                        peptide["sequence"],
                        ph,
                    ).items()
                    if key not in {"sequence"}
                },
            }
            for peptide in peptide_candidates
        ]

        peptide_candidates = annotate_transmembrane_overlap(
            peptide_candidates,
            transmembrane_candidates,
        )
    else:
        peptide_candidates = []

    conservation_columns = []

    if aligned_sequences:
        conservation_columns = calculate_conserved_columns(
            aligned_sequences
        )

    conservation_summary = None

    if aligned_sequences:
        conservation_columns = calculate_conserved_columns(aligned_sequences)
        conservation_summary = calculate_conservation_summary(aligned_sequences)

    return ProteinAnalysisResult(
        sequence=cleaned_sequence,
        length=len(cleaned_sequence),
        composition=composition,
        molecular_weight=molecular_weight,
        gravy=gravy,
        isoelectric_point=isoelectric_point,
        charge_and_hydrophobicity=(
            charge_and_hydrophobicity
        ),
        hydropathy_profile=hydropathy_profile,
        hydrophobic_regions=hydrophobic_regions,
        transmembrane_candidates=(
            transmembrane_candidates
        ),
        localization_evidence=localization_evidence,
        essentiality_evidence=essentiality_evidence,
        host_similarity_evidence=host_similarity_evidence,
        protein_id=protein_id,
        protein_name=protein_name,
        organism=organism,
        accession=accession,
        peptide_candidates=peptide_candidates,
        conservation_columns=conservation_columns,
        conservation_summary=conservation_summary,
    )