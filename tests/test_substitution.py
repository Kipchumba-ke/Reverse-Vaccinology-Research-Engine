import pytest

from app.analysis.substitution import BLOSUM62, blosum62_score

AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"


def test_matrix_covers_every_pair_of_standard_residues():
    assert len(BLOSUM62) == 400

    for a in AMINO_ACIDS:
        for b in AMINO_ACIDS:
            assert (a, b) in BLOSUM62


def test_matrix_is_symmetric():
    for a in AMINO_ACIDS:
        for b in AMINO_ACIDS:
            assert BLOSUM62[(a, b)] == BLOSUM62[(b, a)], (a, b)


@pytest.mark.parametrize(
    "residue, expected",
    [
        ("A", 4), ("R", 5), ("N", 6), ("D", 6), ("C", 9),
        ("Q", 5), ("E", 5), ("G", 6), ("H", 8), ("I", 4),
        ("L", 4), ("K", 5), ("M", 5), ("F", 6), ("P", 7),
        ("S", 4), ("T", 5), ("W", 11), ("Y", 7), ("V", 4),
    ],
)
def test_diagonal_matches_published_values(residue, expected):
    assert blosum62_score(residue, residue) == expected


@pytest.mark.parametrize(
    "a, b, expected",
    [
        ("I", "V", 3), ("I", "L", 2), ("L", "M", 2), ("K", "R", 2),
        ("D", "E", 2), ("F", "Y", 3), ("W", "C", -2), ("W", "G", -2),
        ("D", "L", -4), ("W", "D", -4), ("W", "N", -4), ("W", "P", -4),
        ("S", "T", 1), ("H", "Y", 2), ("A", "S", 1), ("P", "F", -4),
    ],
)
def test_selected_off_diagonal_values_match_published_values(a, b, expected):
    assert blosum62_score(a, b) == expected


def test_similar_residues_outscore_dissimilar_ones():
    assert blosum62_score("I", "V") > blosum62_score("I", "D")
    assert blosum62_score("K", "R") > blosum62_score("K", "E")


def test_unknown_residue_is_rejected():
    with pytest.raises(ValueError):
        blosum62_score("A", "X")
