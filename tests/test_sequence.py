
import pytest

from app.utils.validation import validate_protein_sequence


def test_valid_sequence_is_normalized():
    sequence = "mktii\nals"

    result = validate_protein_sequence(sequence)

    assert result == "MKTIIALS"


def test_empty_sequence_is_rejected():
    with pytest.raises(ValueError):
        validate_protein_sequence("")


def test_invalid_characters_are_rejected():
    with pytest.raises(ValueError):
        validate_protein_sequence("MKTIIALS!")


def test_non_string_input_is_rejected():
    with pytest.raises(TypeError):
        validate_protein_sequence(123)
