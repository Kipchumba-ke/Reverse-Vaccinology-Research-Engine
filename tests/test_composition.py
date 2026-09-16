
import pytest

from app.analysis.composition import (
    calculate_amino_acid_composition,
)


def test_amino_acid_counts():
    result = calculate_amino_acid_composition("MKTII")

    assert result["length"] == 5
    assert result["counts"]["M"] == 1
    assert result["counts"]["I"] == 2
    assert result["counts"]["K"] == 1
    assert result["counts"]["T"] == 1


def test_amino_acid_percentages():
    result = calculate_amino_acid_composition("AAAA")

    assert result["percentages"]["A"] == 100.0


def test_percentages_sum_to_100():
    result = calculate_amino_acid_composition(
        "MKTIIALSYIFCLVFADYKDDDDK"
    )

    total_percentage = sum(
        result["percentages"].values()
    )

    assert total_percentage == pytest.approx(100.0)


def test_empty_sequence_is_rejected():
    with pytest.raises(ValueError):
        calculate_amino_acid_composition("")

def test_all_standard_amino_acids_are_present():
    result = calculate_amino_acid_composition("AAA")

    assert len(result["counts"]) == 20
    assert result["counts"]["A"] == 3
    assert result["counts"]["C"] == 0
    assert result["percentages"]["C"] == 0.0