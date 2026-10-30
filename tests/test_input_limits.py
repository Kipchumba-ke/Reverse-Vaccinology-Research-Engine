import pytest

from app.utils.limits import (
    get_max_alignment_cells,
    get_max_fasta_records,
    get_max_request_bytes,
    get_max_sequence_length,
)
from app.utils.validation import validate_protein_sequence


@pytest.fixture(autouse=True)
def clear_limit_environment(monkeypatch):
    for name in (
        "MAX_SEQUENCE_LENGTH",
        "MAX_FASTA_RECORDS",
        "MAX_ALIGNMENT_CELLS",
        "MAX_REQUEST_BYTES",
    ):
        monkeypatch.delenv(name, raising=False)


def test_default_limits():
    assert get_max_sequence_length() == 5000
    assert get_max_fasta_records() == 50
    assert get_max_alignment_cells() == 4_000_000
    assert get_max_request_bytes() == 2_000_000


def test_limits_can_be_overridden(monkeypatch):
    monkeypatch.setenv("MAX_SEQUENCE_LENGTH", "12")
    monkeypatch.setenv("MAX_FASTA_RECORDS", "3")

    assert get_max_sequence_length() == 12
    assert get_max_fasta_records() == 3


@pytest.mark.parametrize("value", ["abc", "0", "-5"])
def test_invalid_limit_values_are_rejected(monkeypatch, value):
    monkeypatch.setenv("MAX_SEQUENCE_LENGTH", value)

    with pytest.raises(RuntimeError):
        get_max_sequence_length()


def test_blank_limit_uses_the_default(monkeypatch):
    monkeypatch.setenv("MAX_SEQUENCE_LENGTH", "  ")

    assert get_max_sequence_length() == 5000


def test_sequence_at_the_limit_is_accepted(monkeypatch):
    monkeypatch.setenv("MAX_SEQUENCE_LENGTH", "10")

    assert validate_protein_sequence("A" * 10) == "A" * 10


def test_sequence_over_the_limit_is_rejected(monkeypatch):
    monkeypatch.setenv("MAX_SEQUENCE_LENGTH", "10")

    with pytest.raises(ValueError, match="too long"):
        validate_protein_sequence("A" * 11)


def test_whitespace_does_not_count_toward_the_limit(monkeypatch):
    monkeypatch.setenv("MAX_SEQUENCE_LENGTH", "10")

    assert validate_protein_sequence("AAAAA\n AAAAA ") == "A" * 10


def test_fasta_with_too_many_records_is_rejected(monkeypatch):
    from app.input.fasta import parse_fasta_records

    monkeypatch.setenv("MAX_FASTA_RECORDS", "2")
    fasta = ">a\nMKT\n>b\nMKT\n>c\nMKT\n"

    with pytest.raises(ValueError, match="Too many FASTA records"):
        parse_fasta_records(fasta)


def test_fasta_at_the_record_limit_is_accepted(monkeypatch):
    from app.input.fasta import parse_fasta_records

    monkeypatch.setenv("MAX_FASTA_RECORDS", "2")

    assert len(parse_fasta_records(">a\nMKT\n>b\nMKT\n")) == 2


def test_aligner_rejects_sequences_that_are_too_large(monkeypatch):
    from app.analysis.alignment import align_pair

    monkeypatch.setenv("MAX_ALIGNMENT_CELLS", "50")

    with pytest.raises(ValueError, match="too long for the built-in aligner"):
        align_pair("A" * 8, "A" * 8)
