AMINO_ACID_RESIDUE_MASSES = {
    "A": 71.0788,
    "R": 156.1875,
    "N": 114.1038,
    "D": 115.0886,
    "C": 103.1388,
    "E": 129.1155,
    "Q": 128.1307,
    "G": 57.0519,
    "H": 137.1411,
    "I": 113.1594,
    "L": 113.1594,
    "K": 128.1741,
    "M": 131.1926,
    "F": 147.1766,
    "P": 97.1167,
    "S": 87.0782,
    "T": 101.1051,
    "W": 186.2132,
    "Y": 163.1760,
    "V": 99.1326,
}

WATER_MASS = 18.01528

POSITIVELY_CHARGED_AMINO_ACIDS = set("KR")

NEGATIVELY_CHARGED_AMINO_ACIDS = set("DE")

HYDROPHOBIC_AMINO_ACIDS = set("AVILMFWY")

IONIZABLE_GROUP_PKA = {
    "N_TERMINUS": 9.69,
    "C_TERMINUS": 2.34,
    "D": 3.86,
    "E": 4.25,
    "H": 6.00,
    "C": 8.33,
    "Y": 10.07,
    "K": 10.53,
    "R": 12.48,
}


def calculate_molecular_weight(sequence: str) -> float:
    """
    Calculate the approximate molecular weight of
    a linear, unmodified protein sequence.

    Args:
        sequence: A validated protein sequence.

    Returns:
        Molecular weight in Daltons.

    Raises:
        ValueError: If the sequence is empty or contains
        unsupported amino acids.
    """

    if not sequence:
        raise ValueError("Protein sequence cannot be empty.")

    invalid_characters = set(sequence) - set(
        AMINO_ACID_RESIDUE_MASSES
    )

    if invalid_characters:
        invalid = "".join(sorted(invalid_characters))
        raise ValueError(
            f"Invalid amino acid characters found: {invalid}"
        )

    residue_mass = sum(
        AMINO_ACID_RESIDUE_MASSES[amino_acid]
        for amino_acid in sequence
    )

    return residue_mass + WATER_MASS

def calculate_charge_and_hydrophobicity(sequence: str) -> dict:
    """
    Calculate simple charge-related and hydrophobicity
    statistics for a validated protein sequence.

    This is a residue-counting approximation.
    It does not calculate true pH-dependent net charge.
    """

    if not sequence:
        raise ValueError("Protein sequence cannot be empty.")

    invalid_characters = set(sequence) - set(
        AMINO_ACID_RESIDUE_MASSES
    )

    if invalid_characters:
        invalid = "".join(sorted(invalid_characters))
        raise ValueError(
            f"Invalid amino acid characters found: {invalid}"
        )

    sequence_length = len(sequence)

    positively_charged = sum(
        amino_acid in POSITIVELY_CHARGED_AMINO_ACIDS
        for amino_acid in sequence
    )

    negatively_charged = sum(
        amino_acid in NEGATIVELY_CHARGED_AMINO_ACIDS
        for amino_acid in sequence
    )

    hydrophobic_residues = sum(
        amino_acid in HYDROPHOBIC_AMINO_ACIDS
        for amino_acid in sequence
    )

    approximate_net_charge = (
        positively_charged - negatively_charged
    )

    hydrophobicity_percentage = (
        hydrophobic_residues / sequence_length
    ) * 100

    return {
        "positively_charged": positively_charged,
        "negatively_charged": negatively_charged,
        "approximate_net_charge": approximate_net_charge,
        "hydrophobic_residues": hydrophobic_residues,
        "hydrophobicity_percentage": hydrophobicity_percentage,
    }

def calculate_net_charge(sequence: str, ph: float) -> float:
    """
    Estimate the net charge of a protein at a specified pH.

    Uses approximate pKa values and the Henderson–Hasselbalch
    relationship. This is a simplified model and does not
    account for environmental effects on pKa values.
    """

    if not sequence:
        raise ValueError("Protein sequence cannot be empty.")

    if not 0 <= ph <= 14:
        raise ValueError("pH must be between 0 and 14.")

    invalid_characters = set(sequence) - set(
        AMINO_ACID_RESIDUE_MASSES
    )

    if invalid_characters:
        invalid = "".join(sorted(invalid_characters))
        raise ValueError(
            f"Invalid amino acid characters found: {invalid}"
        )

    net_charge = 0.0

    # N-terminal amino group: positively charged when protonated.
    n_terminal_pka = IONIZABLE_GROUP_PKA["N_TERMINUS"]

    net_charge += 1 / (
        1 + 10 ** (ph - n_terminal_pka)
    )

    # C-terminal carboxyl group: negatively charged when deprotonated.
    c_terminal_pka = IONIZABLE_GROUP_PKA["C_TERMINUS"]

    net_charge -= 1 / (
        1 + 10 ** (c_terminal_pka - ph)
    )

    # Side-chain contributions.
    for amino_acid, pka in IONIZABLE_GROUP_PKA.items():
        if amino_acid in {"N_TERMINUS", "C_TERMINUS"}:
            continue

        count = sequence.count(amino_acid)

        if amino_acid in {"K", "R", "H"}:
            # Basic groups become positively charged when protonated.
            net_charge += count / (
                1 + 10 ** (ph - pka)
            )

        elif amino_acid in {"D", "E", "C", "Y"}:
            # Acidic groups become negatively charged when deprotonated.
            net_charge -= count / (
                1 + 10 ** (pka - ph)
            )

    return net_charge

def calculate_isoelectric_point(
    sequence: str,
    tolerance: float = 0.001,
    max_iterations: int = 100,
) -> float:
    """
    Estimate the isoelectric point (pI) of a protein.

    The pI is estimated using binary search to find the pH
    where the calculated net charge approaches zero.

    Args:
        sequence: A validated protein sequence.
        tolerance: Maximum acceptable pH search interval.
        max_iterations: Maximum number of binary-search iterations.

    Returns:
        Estimated isoelectric point.

    Raises:
        ValueError: If the sequence is empty, invalid, tolerance
        is not positive, or max_iterations is invalid.
    """

    if not sequence:
        raise ValueError("Protein sequence cannot be empty.")

    if tolerance <= 0:
        raise ValueError("Tolerance must be greater than zero.")

    if max_iterations <= 0:
        raise ValueError("max_iterations must be greater than zero.")

    invalid_characters = set(sequence) - set(
        AMINO_ACID_RESIDUE_MASSES
    )

    if invalid_characters:
        invalid = "".join(sorted(invalid_characters))
        raise ValueError(
            f"Invalid amino acid characters found: {invalid}"
        )

    low_ph = 0.0
    high_ph = 14.0

    for _ in range(max_iterations):
        mid_ph = (low_ph + high_ph) / 2

        charge = calculate_net_charge(
            sequence,
            mid_ph,
        )

        if charge > 0:
            low_ph = mid_ph
        else:
            high_ph = mid_ph

        if high_ph - low_ph <= tolerance:
            break

    return (low_ph + high_ph) / 2