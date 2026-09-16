
from collections import Counter

STANDARD_AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"

def calculate_amino_acid_composition(sequence: str) -> dict:
    """
    Calculate count and percentage composition of amino acids in a protein sequence.
    """

    sequence_length = len(sequence)

    if sequence_length == 0:
        raise ValueError("Protein sequence cannot be empty.")

    counts = Counter(sequence)

    complete_counts = {
        amino_acid: counts.get(amino_acid, 0)
        for amino_acid in STANDARD_AMINO_ACIDS
    }

    percentages = {
        amino_acid: (count / sequence_length) * 100
        for amino_acid, count in complete_counts.items()
    }

    return {
        "length": sequence_length,
        "counts": complete_counts,
        "percentages": percentages,
    }