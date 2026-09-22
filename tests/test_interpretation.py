from app.analysis.interpretation import (
    interpret_conservation,
    interpret_hydrophobicity,
    interpret_transmembrane_candidates,
    interpret_conserved_regions,
    interpret_localization,
    interpret_essentiality,
)


def test_high_conservation():
    result = interpret_conservation(90)

    assert result.category == "conservation"
    assert result.confidence == "high"


def test_medium_conservation():
    result = interpret_conservation(65)

    assert result.confidence == "medium"


def test_low_conservation():
    result = interpret_conservation(30)

    assert result.confidence == "low"


def test_hydrophobic_sequence():
    result = interpret_hydrophobicity(0.8)

    assert result.category == "hydrophobicity"
    assert result.confidence == "high"


def test_hydrophilic_sequence():
    result = interpret_hydrophobicity(-0.5)

    assert "hydrophilic" in result.interpretation


def test_no_transmembrane_candidates():
    result = interpret_transmembrane_candidates([])

    assert result.category == "membrane_topology"


def test_transmembrane_candidates():
    candidates = [
        {
            "start": 10,
            "end": 30,
        }
    ]

    result = interpret_transmembrane_candidates(candidates)

    assert "One region" in result.interpretation


def test_conserved_regions():
    regions = [
        {
            "start": 10,
            "end": 20,
            "length": 11,
        }
    ]

    result = interpret_conserved_regions(regions)

    assert result.category == "conserved_regions"

def test_interpret_localization_reports_supplied_location():
    evidence = [
        {
            "location": "outer_membrane",
            "source": "localization_database",
            "confidence": "high",
            "description": "Predicted outer membrane localization.",
        }
    ]

    result = interpret_localization(evidence)

    assert result.category == "localization"
    assert "outer_membrane" in result.finding
    assert "outer membrane" in result.interpretation.lower()
    assert result.confidence == "high"

def test_interpret_localization_handles_missing_evidence():
    result = interpret_localization([])

    assert result.category == "localization"
    assert result.confidence == "low"
    assert "No localization evidence supplied" in result.finding
    assert "unavailable" in result.interpretation.lower()

def test_interpret_localization_prefers_highest_confidence():
    evidence = [
        {
            "location": "cytoplasm",
            "source": "database_a",
            "confidence": "low",
            "description": "Low-confidence cytoplasmic localization.",
        },
        {
            "location": "outer_membrane",
            "source": "database_b",
            "confidence": "high",
            "description": "High-confidence outer membrane localization.",
        },
    ]

    result = interpret_localization(evidence)

    assert result.category == "localization"
    assert "outer_membrane" in result.finding
    assert result.confidence == "high"

def test_interpret_localization_does_not_overclaim_biological_significance():
    evidence = [
        {
            "location": "outer_membrane",
            "source": "localization_database",
            "confidence": "high",
            "description": "Predicted outer membrane localization.",
        }
    ]

    result = interpret_localization(evidence)

    assert "outer membrane" in result.interpretation.lower()
    assert "vaccine candidate" not in result.interpretation.lower()
    assert "safety" not in result.interpretation.lower()

def test_interpret_localization_reports_evidence_source():
    evidence = [
        {
            "location": "periplasm",
            "source": "UniProt",
            "confidence": "high",
            "description": "Experimental localization evidence.",
        }
    ]

    result = interpret_localization(evidence)

    assert "UniProt" in result.finding

def test_interpret_localization_preserves_evidence_description():
    evidence = [
        {
            "location": "periplasm",
            "source": "UniProt",
            "confidence": "high",
            "description": "Experimental localization evidence.",
        }
    ]

    result = interpret_localization(evidence)

    assert "Experimental localization evidence." in result.interpretation

def test_interpret_essentiality_reports_essential_status():
    evidence = [
        {
            "gene_id": "gene_001",
            "organism": "Target pathogen",
            "essentiality_status": "essential",
            "source": "essentiality_database",
            "confidence": "high",
            "description": "Gene is required for viability.",
        }
    ]

    result = interpret_essentiality(evidence)

    assert result.category == "essentiality"
    assert "essential" in result.finding
    assert "essential" in result.interpretation.lower()
    assert result.confidence == "high"

def test_interpret_essentiality_reports_non_essential_status():
    evidence = [
        {
            "gene_id": "gene_002",
            "organism": "Target pathogen",
            "essentiality_status": "non-essential",
            "source": "essentiality_database",
            "confidence": "high",
            "description": "Gene is not required for viability under tested conditions.",
        }
    ]

    result = interpret_essentiality(evidence)

    assert result.category == "essentiality"
    assert "non-essential" in result.finding
    assert "non-essential" in result.interpretation.lower()
    assert result.confidence == "high"

def test_interpret_essentiality_reports_conditional_status():
    evidence = [
        {
            "gene_id": "gene_003",
            "organism": "Target pathogen",
            "essentiality_status": "conditionally_essential",
            "source": "essentiality_database",
            "confidence": "medium",
            "description": "Gene is essential under specific tested conditions.",
        }
    ]

    result = interpret_essentiality(evidence)

    assert result.category == "essentiality"
    assert "conditionally_essential" in result.finding
    assert "conditionally essential" in result.interpretation.lower()
    assert result.confidence == "medium"

def test_interpret_essentiality_reports_unknown_status():
    evidence = [
        {
            "gene_id": "gene_004",
            "organism": "Target pathogen",
            "essentiality_status": "unknown",
            "source": "essentiality_database",
            "confidence": "low",
            "description": "No definitive essentiality evidence is available.",
        }
    ]

    result = interpret_essentiality(evidence)

    assert result.category == "essentiality"
    assert "unknown" in result.finding
    assert "unknown" in result.interpretation.lower()
    assert result.confidence == "low"

def test_interpret_essentiality_handles_missing_evidence():
    result = interpret_essentiality([])

    assert result.category == "essentiality"
    assert result.confidence == "low"
    assert "No essentiality evidence supplied" in result.finding
    assert "unavailable" in result.interpretation.lower()

def test_interpret_essentiality_reports_evidence_source():
    evidence = [
        {
            "gene_id": "gene_005",
            "organism": "Target pathogen",
            "essentiality_status": "essential",
            "source": "KEGG",
            "confidence": "high",
            "description": "Gene is required for viability.",
        }
    ]

    result = interpret_essentiality(evidence)

    assert "KEGG" in result.finding

def test_interpret_essentiality_preserves_evidence_description():
    evidence = [
        {
            "gene_id": "gene_006",
            "organism": "Target pathogen",
            "essentiality_status": "essential",
            "source": "KEGG",
            "confidence": "high",
            "description": "Gene is required for viability.",
        }
    ]

    result = interpret_essentiality(evidence)

    assert "Gene is required for viability." in result.interpretation

def test_interpret_essentiality_does_not_overclaim_vaccine_value():
    evidence = [
        {
            "gene_id": "gene_007",
            "organism": "Target pathogen",
            "essentiality_status": "essential",
            "source": "essentiality_database",
            "confidence": "high",
            "description": "Gene is required for viability.",
        }
    ]

    result = interpret_essentiality(evidence)

    assert "vaccine candidate" not in result.interpretation.lower()
    assert "safety" not in result.interpretation.lower()
