from app.utils.validation import validate_protein_sequence


def _substitution_score(
    residue_a: str,
    residue_b: str,
    match_score: int,
    mismatch_score: int,
) -> int:
    if residue_a == residue_b:
        return match_score

    return mismatch_score


def align_pair(
    sequence_a: str,
    sequence_b: str,
    match_score: int = 1,
    mismatch_score: int = -1,
    gap_penalty: int = -1,
) -> dict:
    if not sequence_a or not sequence_b:
        raise ValueError("Sequences cannot be empty.")

    sequence_a = validate_protein_sequence(sequence_a)
    sequence_b = validate_protein_sequence(sequence_b)

    rows = len(sequence_a) + 1
    columns = len(sequence_b) + 1

    score_matrix = [
        [0] * columns
        for _ in range(rows)
    ]

    for i in range(1, rows):
        score_matrix[i][0] = i * gap_penalty

    for j in range(1, columns):
        score_matrix[0][j] = j * gap_penalty

    for i in range(1, rows):
        for j in range(1, columns):
            substitution_score = _substitution_score(
                sequence_a[i - 1],
                sequence_b[j - 1],
                match_score,
                mismatch_score,
            )

            diagonal_score = (
                score_matrix[i - 1][j - 1]
                + substitution_score
            )

            up_score = (
                score_matrix[i - 1][j]
                + gap_penalty
            )

            left_score = (
                score_matrix[i][j - 1]
                + gap_penalty
            )

            score_matrix[i][j] = max(
                diagonal_score,
                up_score,
                left_score,
            )

    aligned_a = []
    aligned_b = []

    i = len(sequence_a)
    j = len(sequence_b)

    while i > 0 or j > 0:
        if i > 0 and j > 0:
            substitution_score = _substitution_score(
                sequence_a[i - 1],
                sequence_b[j - 1],
                match_score,
                mismatch_score,
            )

            if (
                score_matrix[i][j]
                == score_matrix[i - 1][j - 1]
                + substitution_score
            ):
                aligned_a.append(sequence_a[i - 1])
                aligned_b.append(sequence_b[j - 1])
                i -= 1
                j -= 1
                continue

        if (
            i > 0
            and score_matrix[i][j]
            == score_matrix[i - 1][j] + gap_penalty
        ):
            aligned_a.append(sequence_a[i - 1])
            aligned_b.append("-")
            i -= 1
            continue

        aligned_a.append("-")
        aligned_b.append(sequence_b[j - 1])
        j -= 1

    aligned_a.reverse()
    aligned_b.reverse()

    return {
        "sequence_a": "".join(aligned_a),
        "sequence_b": "".join(aligned_b),
        "score": score_matrix[-1][-1],
    }