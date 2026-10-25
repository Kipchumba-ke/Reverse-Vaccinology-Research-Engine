from app.analysis.host_similarity import create_host_similarity_evidence
from app.analysis.blast_runner import run_blastp


def assess_blast_hit_confidence(
    identity_percentage: float,
    alignment_length: int,
    query_coverage_percentage: float,
    subject_coverage_percentage: float,
    e_value: float,
) -> str:
    """Classify the computational strength of a BLAST alignment.

    These thresholds are provisional heuristics, not validated biological
    cutoffs. Confidence describes alignment evidence strength only. It does
    not establish homology, biological safety, or vaccine suitability.
    """

    if (
        e_value <= 1e-10
        and identity_percentage >= 50
        and alignment_length >= 100
        and query_coverage_percentage >= 50
        and subject_coverage_percentage >= 50
    ):
        return "high"

    if (
        e_value <= 1e-3
        and alignment_length >= 100
        and identity_percentage >= 20
        and query_coverage_percentage >= 30
        and subject_coverage_percentage >= 30
    ):
        return "medium"

    return "low"


def parse_blast_hit(
    hit: dict,
    source: str,
    confidence: str,
    description: str,
):
    """Convert a structured BLAST hit into validated evidence.

    The confidence argument is retained for API compatibility.
    Confidence for this BLAST hit is assessed from its alignment metrics.
    """

    assessed_confidence = assess_blast_hit_confidence(
        identity_percentage=hit["identity_percentage"],
        alignment_length=hit["alignment_length"],
        query_coverage_percentage=hit[
            "query_coverage_percentage"
        ],
        subject_coverage_percentage=hit[
            "subject_coverage_percentage"
        ],
        e_value=hit["e_value"],
    )

    return create_host_similarity_evidence(
        target_id=hit["query_id"],
        host_id=hit["subject_id"],
        similarity_method="BLASTP",
        identity_percentage=hit["identity_percentage"],
        alignment_length=hit["alignment_length"],
        query_coverage_percentage=hit[
            "query_coverage_percentage"
        ],
        subject_coverage_percentage=hit[
            "subject_coverage_percentage"
        ],
        e_value=hit["e_value"],
        source=source,
        confidence=assessed_confidence,
        description=description,
    )


def parse_blast_tabular_hit(
    line: str,
    source: str,
    confidence: str,
    description: str,
):
    """Parse one BLAST tabular hit into validated evidence.

    Supports the legacy seven-field format and the eleven-field format
    containing alignment coordinates.
    """

    fields = line.strip().split("\t")

    if len(fields) not in {7, 11}:
        raise ValueError(
            "BLAST tabular hit must contain 7 fields (legacy) "
            "or 11 fields (with alignment coordinates)."
        )

    query_id = fields[0]
    subject_id = fields[1]
    identity_percentage = float(fields[2])
    alignment_length = int(fields[3])
    query_length = int(fields[4])
    subject_length = int(fields[5])
    e_value = float(fields[6])

    if query_length <= 0 or subject_length <= 0:
        raise ValueError(
            "BLAST query and subject sequence length must be greater than zero."
        )

    if len(fields) == 11:
        query_start = int(fields[7])
        query_end = int(fields[8])
        subject_start = int(fields[9])
        subject_end = int(fields[10])

        if not (
            1 <= query_start <= query_end <= query_length
            and 1 <= subject_start <= subject_end <= subject_length
        ):
            raise ValueError(
                "BLAST alignment coordinates must fall within "
                "their respective sequence lengths."
            )

        query_covered_residues = query_end - query_start + 1
        subject_covered_residues = subject_end - subject_start + 1

        query_coverage_percentage = (
            query_covered_residues / query_length
        ) * 100

        subject_coverage_percentage = (
            subject_covered_residues / subject_length
        ) * 100

    else:
        query_coverage_percentage = min(
            (alignment_length / query_length) * 100,
            100.0,
        )

        subject_coverage_percentage = min(
            (alignment_length / subject_length) * 100,
            100.0,
        )

    assessed_confidence = assess_blast_hit_confidence(
        identity_percentage=identity_percentage,
        alignment_length=alignment_length,
        query_coverage_percentage=query_coverage_percentage,
        subject_coverage_percentage=subject_coverage_percentage,
        e_value=e_value,
    )

    return create_host_similarity_evidence(
        target_id=query_id,
        host_id=subject_id,
        similarity_method="BLASTP",
        identity_percentage=identity_percentage,
        alignment_length=alignment_length,
        query_coverage_percentage=query_coverage_percentage,
        subject_coverage_percentage=subject_coverage_percentage,
        e_value=e_value,
        source=source,
        confidence=assessed_confidence,
        description=description,
    )


def parse_blast_tabular_output(
    output: str,
    source: str,
    confidence: str,
    description: str,
):
    """Parse BLAST tabular output into evidence records."""

    if not output.strip():
        return []

    return [
        parse_blast_tabular_hit(
            line,
            source=source,
            confidence=confidence,
            description=description,
        )
        for line in output.strip().splitlines()
    ]


def run_blast_analysis(
    sequence: str,
    database: str,
    source: str,
    confidence: str,
    description: str,
):
    """Run BLASTP and convert its output into evidence records."""

    if not sequence:
        raise ValueError("Sequence is required.")

    if not database:
        raise ValueError("BLAST database is required")

    if confidence not in {"low", "medium", "high"}:
        raise ValueError(
            "Confidence must be one of: low, medium, high"
        )

    output = run_blastp(
        sequence,
        database=database,
    )

    return parse_blast_tabular_output(
        output,
        source=source,
        confidence=confidence,
        description=description,
    )