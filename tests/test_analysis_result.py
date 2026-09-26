from app.models.analysis_result import ProteinAnalysisResult


def test_analysis_result_stores_conservation_columns():
    result = ProteinAnalysisResult(
        sequence="ACDE",
        length=4,
        composition={},
        molecular_weight=0.0,
        gravy=0.0,
        isoelectric_point=7.0,
        charge_and_hydrophobicity={},
        hydropathy_profile=[],
        hydrophobic_regions=[],
        transmembrane_candidates=[],
        localization_evidence=[],
        essentiality_evidence=[],
        host_similarity_evidence=[],
        conservation_columns=[
            {
                "position": 1,
                "consensus": "A",
                "conserved": True,
            }
        ],
    )

    assert result.conservation_columns[0]["position"] == 1


def test_analysis_result_stores_conservation_summary():
    result = ProteinAnalysisResult(
        sequence="ACDE",
        length=4,
        composition={},
        molecular_weight=0.0,
        gravy=0.0,
        isoelectric_point=7.0,
        charge_and_hydrophobicity={},
        hydropathy_profile=[],
        hydrophobic_regions=[],
        transmembrane_candidates=[],
        localization_evidence=[],
        essentiality_evidence=[],
        host_similarity_evidence=[],
        conservation_summary={
            "sequence_count": 2,
            "alignment_length": 5,
            "mean_identity": 75.0,
            "conserved_positions": 3,
            "conservation_percentage": 60.0,
        },
    )

    assert result.conservation_summary["sequence_count"] == 2