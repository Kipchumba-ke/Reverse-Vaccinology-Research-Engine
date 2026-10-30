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

# Residue groups used by Clustal Omega to mark similar alignment columns.
# A column is "strongly similar" when every residue in it belongs to one
# strong group (Clustal's ":" symbol) and "weakly similar" when every residue
# belongs to one weak group (Clustal's "." symbol).
STRONG_SIMILARITY_GROUPS = tuple(
    frozenset(group)
    for group in (
        "STA", "NEQK", "NHQK", "NDEQ", "QHRK",
        "MILV", "MILF", "HY", "FYW",
    )
)

WEAK_SIMILARITY_GROUPS = tuple(
    frozenset(group)
    for group in (
        "CSA", "ATV", "SAG", "STNK", "STPA", "SGND",
        "SNDEQK", "NDEQHK", "NEQHRK", "FVLIM", "HFY",
    )
)


def classify_column_similarity(residues: list[str]) -> str:
    """Classify one alignment column by residue similarity.

    Returns "gapped" when any sequence has a gap, otherwise "identical",
    "strongly_similar", "weakly_similar" or "variable".
    """

    if not residues:
        raise ValueError("A column needs at least one residue.")

    if GAP_CHARACTER in residues:
        return "gapped"

    distinct = set(residues)

    if len(distinct) == 1:
        return "identical"

    if any(distinct <= group for group in STRONG_SIMILARITY_GROUPS):
        return "strongly_similar"

    if any(distinct <= group for group in WEAK_SIMILARITY_GROUPS):
        return "weakly_similar"

    return "variable"


def calculate_similarity_summary(sequences: list[str]) -> dict:
    """Summarise similarity across an alignment, not only exact identity.

    Identity alone treats a change from leucine to isoleucine like a change
    from leucine to aspartate. This summary also counts columns whose
    residues share a biochemical group.
    """

    if not sequences:
        raise ValueError("At least one sequence is required.")

    if any(not sequence for sequence in sequences):
        raise ValueError("Sequences cannot be empty.")

    alignment_length = len(sequences[0])

    if any(len(sequence) != alignment_length for sequence in sequences):
        raise ValueError("All aligned sequences must have the same length.")

    counts = {
        "identical": 0,
        "strongly_similar": 0,
        "weakly_similar": 0,
        "variable": 0,
        "gapped": 0,
    }

    for position in range(alignment_length):
        column = [sequence[position] for sequence in sequences]
        counts[classify_column_similarity(column)] += 1

    def percentage(count: int) -> float:
        return count / alignment_length * 100

    return {
        "alignment_length": alignment_length,
        "sequence_count": len(sequences),
        "identical_columns": counts["identical"],
        "strongly_similar_columns": counts["strongly_similar"],
        "weakly_similar_columns": counts["weakly_similar"],
        "variable_columns": counts["variable"],
        "gapped_columns": counts["gapped"],
        "identical_percentage": percentage(counts["identical"]),
        "identical_or_strongly_similar_percentage": percentage(
            counts["identical"] + counts["strongly_similar"]
        ),
        "method": "Clustal Omega similarity groups",
    }
