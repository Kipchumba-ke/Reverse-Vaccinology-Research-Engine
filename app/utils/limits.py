"""Input size limits that protect the server from oversized requests.

Each limit can be changed with an environment variable:
    MAX_SEQUENCE_LENGTH    residues per protein sequence (default 5000)
    MAX_FASTA_RECORDS      records per FASTA submission (default 50)
    MAX_ALIGNMENT_CELLS    length(a) x length(b) for the built-in aligner
                           (default 4,000,000, about 2000 x 2000 residues)
    MAX_REQUEST_BYTES      HTTP request body size (default 2,000,000)
"""

import os


DEFAULT_MAX_SEQUENCE_LENGTH = 5000
DEFAULT_MAX_FASTA_RECORDS = 50
DEFAULT_MAX_ALIGNMENT_CELLS = 4_000_000
DEFAULT_MAX_REQUEST_BYTES = 2_000_000


def _read_positive_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name)

    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = int(raw_value)
    except ValueError as error:
        raise RuntimeError(f"{name} must be a whole number.") from error

    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero.")

    return value


def get_max_sequence_length() -> int:
    return _read_positive_int(
        "MAX_SEQUENCE_LENGTH",
        DEFAULT_MAX_SEQUENCE_LENGTH,
    )


def get_max_fasta_records() -> int:
    return _read_positive_int(
        "MAX_FASTA_RECORDS",
        DEFAULT_MAX_FASTA_RECORDS,
    )


def get_max_alignment_cells() -> int:
    return _read_positive_int(
        "MAX_ALIGNMENT_CELLS",
        DEFAULT_MAX_ALIGNMENT_CELLS,
    )


def get_max_request_bytes() -> int:
    return _read_positive_int(
        "MAX_REQUEST_BYTES",
        DEFAULT_MAX_REQUEST_BYTES,
    )
