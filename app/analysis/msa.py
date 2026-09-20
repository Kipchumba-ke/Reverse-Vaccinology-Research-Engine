from app.analysis.alignment import align_pair
from app.utils.validation import validate_protein_sequence


def align_sequences(sequences: list[str]) -> list[str]:
    if not sequences:
        raise ValueError("At least one sequence is required.")

    validated_sequences = [
        validate_protein_sequence(sequence)
        for sequence in sequences
    ]

    reference = validated_sequences[0]

    pairwise_alignments = [
        align_pair(reference, sequence)
        for sequence in validated_sequences
    ]

    insertion_counts = {}

    for alignment in pairwise_alignments:
        aligned_reference = alignment["sequence_a"]

        reference_position = 0
        consecutive_gaps = 0

        for residue in aligned_reference:
            if residue == "-":
                consecutive_gaps += 1
            else:
                if consecutive_gaps:
                    insertion_counts[reference_position] = max(
                        insertion_counts.get(reference_position, 0),
                        consecutive_gaps,
                    )
                    consecutive_gaps = 0

                reference_position += 1

        if consecutive_gaps:
            insertion_counts[reference_position] = max(
                insertion_counts.get(reference_position, 0),
                consecutive_gaps,
            )

    result = []

    for alignment in pairwise_alignments:
        aligned_reference = alignment["sequence_a"]
        aligned_sequence = alignment["sequence_b"]

        result.append(
            _merge_alignment(
                reference,
                aligned_reference,
                aligned_sequence,
                insertion_counts,
            )
        )

    return result


def _merge_alignment(
    reference: str,
    aligned_reference: str,
    aligned_sequence: str,
    insertion_counts: dict[int, int],
) -> str:
    result = []
    alignment_position = 0

    for reference_position in range(len(reference) + 1):
        insertion_count = insertion_counts.get(reference_position, 0)

        for _ in range(insertion_count):
            if (
                alignment_position < len(aligned_reference)
                and aligned_reference[alignment_position] == "-"
            ):
                result.append(aligned_sequence[alignment_position])
                alignment_position += 1
            else:
                result.append("-")

        if reference_position < len(reference):
            while (
                alignment_position < len(aligned_reference)
                and aligned_reference[alignment_position] == "-"
            ):
                alignment_position += 1

            result.append(aligned_sequence[alignment_position])
            alignment_position += 1

    return "".join(result)