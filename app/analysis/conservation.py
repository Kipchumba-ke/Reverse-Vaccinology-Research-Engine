from app.models.conservation import ConservationResult
from collections import Counter

GAP_CHARACTER = "-"


def calculate_pairwise_identity(
    sequence_a: str,
    sequence_b: str,
) -> float:
    """
    Calculate percentage identity between two aligned sequences.

    Both sequences must have the same length.
    """

    if not sequence_a or not sequence_b:
        raise ValueError(
            "Sequences cannot be empty."
        )

    if len(sequence_a) != len(sequence_b):
        raise ValueError(
            "Aligned sequences must have the same length."
        )

    comparable_positions = 0
    identical_positions = 0

    for amino_acid_a, amino_acid_b in zip(sequence_a, sequence_b):
        if (
            amino_acid_a == GAP_CHARACTER
            or amino_acid_b == GAP_CHARACTER
        ):
            continue
        comparable_positions += 1

        if amino_acid_a == amino_acid_b:
            identical_positions += 1

    if comparable_positions == 0:
        raise ValueError(
            "No comparable positions found between the sequences."
        )

    return (
        identical_positions / comparable_positions
    ) * 100

def calculate_conserved_columns(
    sequences: list[str],
) -> list[dict]:
    """
    Identify conserved positions in a multiple sequence alignment.

    A position is considered fully conserved when every sequence
    contains the same amino acid at that position.

    Sequences must already be aligned and therefore have equal length.
    """

    if not sequences:
        raise ValueError(
            "At least one sequence is required."
        )

    if any(not sequence for sequence in sequences):
        raise ValueError(
            "Sequences cannot be empty."
        )

    alignment_length = len(sequences[0])

    if any(
        len(sequence) != alignment_length
        for sequence in sequences
    ):
        raise ValueError(
            "All aligned sequences must have the same length."
        )

    conserved_columns = []

    for position in range(alignment_length):
        column = [
            sequence[position]
            for sequence in sequences
        ]

        amino_acids = [
            residue
            for residue in column
            if residue != GAP_CHARACTER
        ]

        gap_count = column.count(GAP_CHARACTER)

        if amino_acids:
            counts = Counter(amino_acids)
            consensus, consensus_count = counts.most_common(1)[0]

            conservation_percentage = (
                consensus_count / len(amino_acids)
            ) * 100
        else:
            consensus = None
            conservation_percentage = 0.0

        fully_conserved = (
            gap_count == 0
            and len(set(amino_acids)) == 1
        )

        conserved_columns.append({
            "position": position + 1,
            "amino_acids": column,
            "consensus": consensus,
            "conserved" : fully_conserved,
            "conservation_percentage": (
                conservation_percentage
                ),
            "gap_count": gap_count,
            "gap_percentage": (
                gap_count / len(sequences)
            ) * 100,
        })

    return conserved_columns

def calculate_conservation_summary(
    sequences: list[str],
) -> ConservationResult:
    """
    Calculate a summary of conservation across an aligned
    set of protein sequences.
    """

    if not sequences:
        raise ValueError(
            "At least one sequence is required."
        )

    if any(not sequence for sequence in sequences):
        raise ValueError(
            "Sequences cannot be empty."
        )

    alignment_length = len(sequences[0])

    if any(
        len(sequence) != alignment_length
        for sequence in sequences
    ):
        raise ValueError(
            "All aligned sequences must have the same length."
        )

    conserved_columns = calculate_conserved_columns(
        sequences
    )

    conserved_positions = sum(
        column["conserved"]
        for column in conserved_columns
    )

    conservation_percentage = (
        conserved_positions / alignment_length
    ) * 100

    pairwise_identities = []

    for index, sequence_a in enumerate(sequences):
        for sequence_b in sequences[index + 1:]:
            identity = calculate_pairwise_identity(
                sequence_a,
                sequence_b,
            )

            pairwise_identities.append(identity)

    if pairwise_identities:
        mean_identity = (
            sum(pairwise_identities)
            / len(pairwise_identities)
        )
    else:
        mean_identity = 100.0

    return ConservationResult(
        sequence_count=len(sequences),
        alignment_length=alignment_length,
        mean_identity=mean_identity,
        conserved_positions=conserved_positions,
        conservation_percentage=conservation_percentage,
    )

def find_conserved_regions(
    conserved_columns: list[dict],
    min_length: int = 1,
) -> list[dict]:
    """
    Group adjacent conserved alignment columns into regions.

    Args:
        conserved_columns: Output from calculate_conserved_columns().
        min_length: Minimum number of consecutive conserved positions
            required for a region.

    Returns:
        A list of conserved regions.
    """

    if min_length <= 0:
        raise ValueError(
            "Minimum region length must be greater than zero."
        )

    regions = []
    current_start = None
    current_end = None
    current_consensus = []

    for column in conserved_columns:
        position = column["position"]
        conserved = column["conserved"]

        if conserved:
            if current_start is None:
                current_start = position

            current_end = position
            current_consensus.append(column["consensus"])

        else:
            if current_start is not None:
                region_length = (
                    current_end - current_start + 1
                )

                if region_length >= min_length:
                    regions.append({
                        "start": current_start,
                        "end": current_end,
                        "length": region_length,
                        "consensus": "".join(current_consensus),
                    })

                current_start = None
                current_end = None
                current_consensus = []

    if current_start is not None:
        region_length = (
            current_end - current_start + 1
        )

        if region_length >= min_length:
            regions.append({
                "start": current_start,
                "end": current_end,
                "length": region_length,
                "consensus": "".join(current_consensus),
            })

    return regions