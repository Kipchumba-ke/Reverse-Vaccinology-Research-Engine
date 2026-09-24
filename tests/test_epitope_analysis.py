from app.analysis.epitope import generate_peptide_windows
from app.analysis.epitope import (
    generate_peptide_windows,
    calculate_peptide_properties,
)
from app.analysis.epitope import annotate_conservation_overlap

def test_generate_peptide_windows_returns_overlapping_windows():
    result = generate_peptide_windows(
        "ABCDEFGHIJ",
        window_size=4,
    )

    assert result == [
        {"start": 1, "end": 4, "sequence": "ABCD"},
        {"start": 2, "end": 5, "sequence": "BCDE"},
        {"start": 3, "end": 6, "sequence": "CDEF"},
        {"start": 4, "end": 7, "sequence": "DEFG"},
        {"start": 5, "end": 8, "sequence": "EFGH"},
        {"start": 6, "end": 9, "sequence": "FGHI"},
        {"start": 7, "end": 10, "sequence": "GHIJ"},
    ]



def test_calculate_peptide_properties():
    result = calculate_peptide_properties(
        "AKDE",
        ph=7.0,
    )

    assert result["sequence"] == "AKDE"
    assert result["length"] == 4
    assert "gravy" in result
    assert "net_charge" in result


from app.analysis.epitope import annotate_transmembrane_overlap


def test_annotate_transmembrane_overlap():
    peptides = [
        {"start": 1, "end": 5, "sequence": "ABCDE"},
        {"start": 6, "end": 10, "sequence": "FGHIJ"},
    ]

    transmembrane_regions = [
        {"start": 4, "end": 8},
    ]

    result = annotate_transmembrane_overlap(
        peptides,
        transmembrane_regions,
    )

    assert result == [
        {
            "start": 1,
            "end": 5,
            "sequence": "ABCDE",
            "overlaps_transmembrane": True,
        },
        {
            "start": 6,
            "end": 10,
            "sequence": "FGHIJ",
            "overlaps_transmembrane": True,
        },
    ]



def test_annotate_conservation_overlap():
    peptides = [
        {"start": 1, "end": 5, "sequence": "ABCDE"},
        {"start": 6, "end": 10, "sequence": "FGHIJ"},
    ]

    conserved_regions = [
        {"start": 4, "end": 7, "length": 4, "consensus": "DEFG"},
    ]

    result = annotate_conservation_overlap(
        peptides,
        conserved_regions,
    )

    assert result == [
        {
            "start": 1,
            "end": 5,
            "sequence": "ABCDE",
            "overlaps_conserved_region": True,
        },
        {
            "start": 6,
            "end": 10,
            "sequence": "FGHIJ",
            "overlaps_conserved_region": True,
        },
    ]