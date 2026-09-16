import pytest

from app.analysis.properties import (
    calculate_molecular_weight,
    calculate_charge_and_hydrophobicity,
    calculate_net_charge,
    calculate_isoelectric_point
)


def test_molecular_weight_of_single_amino_acid():
    result = calculate_molecular_weight("A")

    assert result == pytest.approx(89.09408)


def test_molecular_weight_of_two_amino_acids():
    result = calculate_molecular_weight("AA")

    assert result == pytest.approx(160.17288)


def test_molecular_weight_is_rejected_for_empty_sequence():
    with pytest.raises(ValueError):
        calculate_molecular_weight("")
        


def test_invalid_amino_acids_are_rejected():
    with pytest.raises(ValueError):
        calculate_molecular_weight("MKT!")


def test_molecular_weight_increases_with_sequence_length():
    short_sequence = calculate_molecular_weight("AAAA")
    long_sequence = calculate_molecular_weight("AAAAAAAA")

    assert long_sequence > short_sequence

def test_charge_and_hydrophobicity_statistics():
    result = calculate_charge_and_hydrophobicity(
        "AKRDEAV"
    )

    assert result["positively_charged"] == 2
    assert result["negatively_charged"] == 2
    assert result["approximate_net_charge"] == 0
    assert result["hydrophobic_residues"] == 3
    assert result["hydrophobicity_percentage"] == pytest.approx(
        42.8571428571
    )

def test_net_charge_is_positive_at_low_ph():
    result = calculate_net_charge("AKRDE", ph=2)

    assert result > 0


def test_net_charge_is_negative_at_high_ph():
    result = calculate_net_charge("AKRDE", ph=12)

    assert result < 0


def test_invalid_ph_is_rejected():
    with pytest.raises(ValueError):
        calculate_net_charge("AKRDE", ph=15)


def test_net_charge_changes_with_ph():
    low_ph_charge = calculate_net_charge("AKRDE", ph=2)
    high_ph_charge = calculate_net_charge("AKRDE", ph=12)

    assert low_ph_charge > high_ph_charge

def test_isoelectric_point_is_within_ph_range():
    result = calculate_isoelectric_point("AKRDE")

    assert 0 <= result <= 14


def test_isoelectric_point_tolerance_must_be_positive():
    with pytest.raises(ValueError):
        calculate_isoelectric_point(
            "AKRDE",
            tolerance=0,
        )


def test_isoelectric_point_max_iterations_must_be_positive():
    with pytest.raises(ValueError):
        calculate_isoelectric_point(
            "AKRDE",
            max_iterations=0,
        )


def test_isoelectric_point_has_near_zero_charge():
    result = calculate_isoelectric_point("AKRDE")

    charge = calculate_net_charge(
        "AKRDE",
        result,
    )

    assert abs(charge) < 0.01