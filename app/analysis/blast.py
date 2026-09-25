from app.analysis.host_similarity import create_host_similarity_evidence


def parse_blast_hit(
    hit: dict,
    source: str,
    confidence: str,
    description: str,
):
    return create_host_similarity_evidence(
        target_id=hit["query_id"],
        host_id=hit["subject_id"],
        similarity_method="BLASTP",
        identity_percentage=hit["identity_percentage"],
        alignment_length=hit["alignment_length"],
        query_coverage_percentage=hit["query_coverage_percentage"],
        subject_coverage_percentage=hit["subject_coverage_percentage"],
        e_value=hit["e_value"],
        source=source,
        confidence=confidence,
        description=description,
    )

def parse_blast_tabular_hit(
    line: str,
    source: str,
    confidence: str,
    description: str,
):
    fields = line.strip().split("\t")

    if len(fields) != 7:
        raise ValueError(
            "BLAST tabular hit must contain 7 fields."
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

    query_coverage_percentage = (
        alignment_length / query_length
    ) * 100

    subject_coverage_percentage = (
        alignment_length / subject_length
    ) * 100

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
        confidence=confidence,
        description=description,
    )
