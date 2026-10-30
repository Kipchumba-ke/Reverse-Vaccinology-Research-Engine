from app.utils.limits import get_max_sequence_length


STANDARD_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")


def validate_protein_sequence(sequence: str) -> str:
    """
    Validate and normalize a protein sequence.

    """

    if not isinstance(sequence, str):
        raise TypeError("Protein sequence must be a string.")

    cleaned_sequence = "".join(sequence.split()).upper()

    if not cleaned_sequence:
        raise ValueError("Protein sequence cannot be empty.")

    maximum_length = get_max_sequence_length()

    if len(cleaned_sequence) > maximum_length:
        raise ValueError(
            "Protein sequence is too long "
            f"(maximum {maximum_length} residues)."
        )

    invalid_characters = set(cleaned_sequence) - STANDARD_AMINO_ACIDS

    if invalid_characters:
        invalid = "".join(sorted(invalid_characters))
        raise ValueError(
            f"Invalid amino acid characters found: {invalid}"
        )

    return cleaned_sequence
