import pytest

from app.input.fasta import (
    load_fasta_file,
    parse_fasta,
    parse_fasta_records,
)

def test_parse_single_protein_fasta():
    fasta = ">protein_1\nMKTIIALSYIFCLVFAD\n"

    record = parse_fasta(fasta)

    assert record["id"] == "protein_1"
    assert record["sequence"] == "MKTIIALSYIFCLVFAD"


def test_parse_fasta_rejects_input_without_header():
    fasta = "MKTIIALSYIFCLVFAD"

    with pytest.raises(ValueError, match="Invalid FASTA input"):
        parse_fasta(fasta)

def test_parse_multiline_protein_fasta():
    fasta = (
        ">protein_1\n"
        "MKTIIALSYI\n"
        "FCLVFAD\n"
    )

    record = parse_fasta(fasta)

    assert record["id"] == "protein_1"
    assert record["sequence"] == "MKTIIALSYIFCLVFAD"

def test_parse_fasta_rejects_multiple_records():
    fasta = (
        ">protein_1\n"
        "MKTIIALSYI\n"
        ">protein_2\n"
        "FCLVFAD\n"
    )

    with pytest.raises(
        ValueError,
        match="Multiple FASTA records are not supported",
    ):
        parse_fasta(fasta)

def test_parse_fasta_rejects_empty_sequence():
    fasta = ">protein_1\n"

    with pytest.raises(
        ValueError,
        match="FASTA sequence cannot be empty",
    ):
        parse_fasta(fasta)

def test_parse_fasta_normalizes_sequence():
    fasta = (
        ">protein_1\n"
        "mktii\n"
        "als\n"
    )

    record = parse_fasta(fasta)

    assert record["sequence"] == "MKTIIALS"

def test_parse_fasta_rejects_invalid_protein_sequence():
    fasta = (
        ">protein_1\n"
        "MKTIIALS!\n"
    )

    with pytest.raises(ValueError):
        parse_fasta(fasta)

def test_load_fasta_file(tmp_path):
    fasta_file = tmp_path / "protein.fasta"

    fasta_file.write_text(
        ">protein_1\n"
        "MKTIIALSYIFCLVFAD\n"
    )

    record = load_fasta_file(fasta_file)

    assert record["id"] == "protein_1"
    assert record["sequence"] == "MKTIIALSYIFCLVFAD"

def test_parse_fasta_rejects_empty_identifier():
    fasta = (
        ">\n"
        "MKTIIALSYIFCLVFAD\n"
    )

    with pytest.raises(ValueError, match="FASTA identifier cannot be empty"):
        parse_fasta(fasta)

def test_parse_fasta_records_multiple_records():
    fasta_text = """>protein_1
MKT
>protein_2
MKTT
>protein_3
MKT
"""

    result = parse_fasta_records(fasta_text)

    assert result == [
        {
            "id": "protein_1",
            "description": "",
            "organism": None,
            "accession": None,
            "sequence": "MKT"
        },
        {
            "id": "protein_2",
            "description": "",
            "organism": None,
            "accession": None,
            "sequence": "MKTT",
        },
        {
            "id": "protein_3",
            "description": "",
            "organism": None,
            "accession": None,
            "sequence": "MKT"
        },
    ]

def test_parse_fasta_records_rejects_missing_sequence():
    fasta_text = """>protein_1
MKT
>protein_2
"""

    with pytest.raises(
        ValueError,
        match="FASTA sequence cannot be empty",
    ):
        parse_fasta_records(fasta_text)

def test_parse_fasta_records_rejects_empty_identifier():
    fasta_text = """>
MKT
"""

    with pytest.raises(
        ValueError,
        match="FASTA identifier cannot be empty",
    ):
        parse_fasta_records(fasta_text)


def test_parse_fasta_records_rejects_invalid_sequence():
    fasta_text = """>protein_1
MKT
>protein_2
MKXZ
"""

    with pytest.raises(
        ValueError,
        match="Invalid amino acid characters found",
    ):
        parse_fasta_records(fasta_text)


def test_parse_fasta_records_can_feed_msa():
    from app.analysis.msa import align_sequences

    fasta_text = """>protein_1
MKT
>protein_2
MKTT
>protein_3
MKT
"""

    records = parse_fasta_records(fasta_text)
    sequences = [record["sequence"] for record in records]

    alignment = align_sequences(sequences)

    assert alignment == [
        "MK-T",
        "MKTT",
        "MK-T",
    ]


def test_parse_fasta_records_can_feed_msa_and_conservation():
    from app.analysis.conservation import calculate_conservation_summary
    from app.analysis.msa import align_sequences

    fasta_text = """>protein_1
MKT
>protein_2
MKTT
>protein_3
MKT
"""

    records = parse_fasta_records(fasta_text)
    sequences = [record["sequence"] for record in records]

    alignment = align_sequences(sequences)
    summary = calculate_conservation_summary(alignment)

    assert summary.sequence_count == 3
    assert summary.alignment_length == 4
    assert summary.conserved_positions == 3
    assert summary.conservation_percentage == 75.0
    assert summary.mean_identity == 100.0


def test_parse_fasta_preserves_header_description():
    fasta_text = (
        ">protein_123 Example protein\n"
        "MKTIIALSYIFCLVFAD\n"
    )

    record = parse_fasta(fasta_text)

    assert record["id"] == "protein_123"
    assert record["description"] == "Example protein"


def test_parse_fasta_extracts_organism_from_description():
    fasta_text = (
        ">protein_123 Example protein OS=Escherichia coli\n"
        "MKTIIALSYIFCLVFAD\n"
    )

    record = parse_fasta(fasta_text)

    assert record["id"] == "protein_123"
    assert record["description"] == "Example protein OS=Escherichia coli"
    assert record["organism"] == "Escherichia coli"


def test_parse_fasta_extracts_accession_from_uniprot_style_header():
    fasta_text = (
        ">sp|P12345|EXAMPLE_PROTEIN Example protein OS=Escherichia coli\n"
        "MKTIIALSYIFCLVFAD\n"
    )

    record = parse_fasta(fasta_text)

    assert record["id"] == "sp|P12345|EXAMPLE_PROTEIN"
    assert record["description"] == "Example protein OS=Escherichia coli"
    assert record["organism"] == "Escherichia coli"
    assert record["accession"] == "P12345"