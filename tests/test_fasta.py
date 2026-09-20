import pytest

from app.input.fasta import (
    load_fasta_file,
    parse_fasta,
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