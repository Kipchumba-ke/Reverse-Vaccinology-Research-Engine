from app.analysis.interpretation import (
    interpret_conservation,
    interpret_hydrophobicity,
    interpret_transmembrane_candidates,
    interpret_conserved_regions,
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