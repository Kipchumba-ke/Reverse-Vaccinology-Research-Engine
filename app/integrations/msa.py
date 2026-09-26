import subprocess


def _parse_alignment(output: str) -> list[str]:
    sequences = []
    current_sequence = []

    for line in output.strip().splitlines():
        if line.startswith(">"):
            if current_sequence:
                sequences.append("".join(current_sequence))
                current_sequence = []
        else:
            current_sequence.append(line.strip())

    if current_sequence:
        sequences.append("".join(current_sequence))

    return sequences

def run_msa(sequences: list[str]) -> list[str]:
    if len(sequences) < 2:
        raise ValueError("At least two sequences are required")

    try:
        result = subprocess.run(
            ["clustalo"],
            input="".join(
                f">seq{i}\n{sequence}\n"
                for i, sequence in enumerate(sequences, start=1)
            ),
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Clustal Omega executable not found") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("MSA execution failed") from exc

    if not result.stdout.strip():
        raise RuntimeError("MSA returned no alignment")

    return _parse_alignment(result.stdout)