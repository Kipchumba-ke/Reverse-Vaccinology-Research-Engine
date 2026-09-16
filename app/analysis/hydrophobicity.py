KYTE_DOOLITTLE_SCALE = {
    "I": 4.5,
    "V": 4.2,
    "L": 3.8,
    "F": 2.8,
    "C": 2.5,
    "M": 1.9,
    "A": 1.8,
    "G": -0.4,
    "T": -0.7,
    "S": -0.8,
    "W": -0.9,
    "Y": -1.3,
    "P": -1.6,
    "H": -3.2,
    "E": -3.5,
    "Q": -3.5,
    "D": -3.5,
    "N": -3.5,
    "K": -3.9,
    "R": -4.5,
}


def calculate_gravy(sequence: str) -> float:
    """
    Calculate the GRAVY (Grand Average of Hydropathy)
    score using the Kyte-Doolittle scale.

    GRAVY is the average hydropathy value of all
    amino acids in the sequence.

    Positive values generally indicate greater
    hydrophobic character, while negative values
    indicate greater hydrophilic character.
    """

    if not sequence:
        raise ValueError("Protein sequence cannot be empty.")

    invalid_characters = set(sequence) - set(
        KYTE_DOOLITTLE_SCALE
    )

    if invalid_characters:
        invalid = "".join(sorted(invalid_characters))
        raise ValueError(
            f"Invalid amino acid characters found: {invalid}"
        )

    total_hydropathy = sum(
        KYTE_DOOLITTLE_SCALE[amino_acid]
        for amino_acid in sequence
    )

    return total_hydropathy / len(sequence)

def calculate_hydropathy_profile(
    sequence: str,
    window_size: int = 19,
) -> list[dict]:
    """
    Calculate a sliding-window Kyte-Doolittle hydropathy profile.

    Args:
        sequence: A validated protein sequence.
        window_size: Number of residues included in each window.

    Returns:
        A list containing the starting position, ending position,
        and average hydropathy for each window.
    """

    if not sequence:
        raise ValueError("Protein sequence cannot be empty.")

    if window_size <= 0:
        raise ValueError("Window size must be greater than zero.")

    if window_size > len(sequence):
        raise ValueError(
            "Window size cannot be greater than sequence length."
        )

    invalid_characters = set(sequence) - set(
        KYTE_DOOLITTLE_SCALE
    )

    if invalid_characters:
        invalid = "".join(sorted(invalid_characters))
        raise ValueError(
            f"Invalid amino acid characters found: {invalid}"
        )

    profile = []

    for start in range(
        len(sequence) - window_size + 1
    ):
        end = start + window_size

        window = sequence[start:end]

        average_hydropathy = sum(
            KYTE_DOOLITTLE_SCALE[amino_acid]
            for amino_acid in window
        ) / window_size

        profile.append({
            "start": start + 1,
            "end": end,
            "hydropathy": average_hydropathy,
        })

    return profile

def find_hydrophobic_regions(
    sequence: str,
    window_size: int = 19,
    threshold: float = 1.6,
) -> list[dict]:
    """
    Identify windows with average Kyte-Doolittle
    hydropathy above a specified threshold.

    This identifies hydrophobic regions only.
    It does not by itself establish that a region
    is a transmembrane helix.
    """

    if threshold < -4.5 or threshold > 4.5:
        raise ValueError(
            "Threshold must be between -4.5 and 4.5."
        )

    profile = calculate_hydropathy_profile(
        sequence,
        window_size,
    )

    hydrophobic_regions = [
        window
        for window in profile
        if window["hydropathy"] >= threshold
    ]

    return hydrophobic_regions

def merge_hydrophobic_regions(
    regions: list[dict],
) -> list[dict]:
    """
    Merge overlapping or directly adjacent hydrophobic windows
    into continuous regions.

    Args:
        regions: Hydrophobic windows returned by
            find_hydrophobic_regions().

    Returns:
        A list of merged continuous regions.
    """

    if not regions:
        return []

    sorted_regions = sorted(
        regions,
        key=lambda region: region["start"],
    )

    merged = [
        {
            "start": sorted_regions[0]["start"],
            "end": sorted_regions[0]["end"],
        }
    ]

    for region in sorted_regions[1:]:
        current = merged[-1]

        if region["start"] <= current["end"] + 1:
            current["end"] = max(
                current["end"],
                region["end"],
            )
        else:
            merged.append({
                "start": region["start"],
                "end": region["end"],
            })

    return merged

def summarize_hydrophobic_regions(
    sequence: str,
    regions: list[dict],
) -> list[dict]:
    """
    Add biological measurements to merged hydrophobic regions.

    Each region receives:
        - start position
        - end position
        - length
        - sequence
        - average hydropathy

    Args:
        sequence: Protein sequence.
        regions: Merged hydrophobic regions.

    Returns:
        A list of summarized hydrophobic regions.
    """

    if not sequence:
        raise ValueError("Protein sequence cannot be empty.")

    invalid_characters = set(sequence) - set(
        KYTE_DOOLITTLE_SCALE
    )

    if invalid_characters:
        invalid = "".join(sorted(invalid_characters))
        raise ValueError(
            f"Invalid amino acid characters found: {invalid}"
        )

    summaries = []

    for region in regions:
        start = region["start"]
        end = region["end"]

        if start < 1 or end > len(sequence):
            raise ValueError(
                "Region coordinates are outside the sequence."
            )

        if start > end:
            raise ValueError(
                "Region start cannot be greater than end."
            )

        region_sequence = sequence[start - 1:end]

        average_hydropathy = sum(
            KYTE_DOOLITTLE_SCALE[amino_acid]
            for amino_acid in region_sequence
        ) / len(region_sequence)

        summaries.append({
            "start": start,
            "end": end,
            "length": len(region_sequence),
            "sequence": region_sequence,
            "average_hydropathy": average_hydropathy,
        })

    return summaries

def classify_transmembrane_candidates(
    regions: list[dict],
    min_length: int = 18,
    max_length: int = 25,
    min_hydropathy: float = 1.6,
) -> list[dict]:
    """
    Classify summarized hydrophobic regions as candidate
    transmembrane segments based on length and hydropathy.

    This is a heuristic classifier. It does not establish
    that a region is experimentally confirmed to be a
    transmembrane helix.
    """

    if min_length <= 0:
        raise ValueError(
            "min_length must be greater than zero."
        )

    if max_length < min_length:
        raise ValueError(
            "max_length cannot be less than min_length."
        )

    if min_hydropathy < -4.5 or min_hydropathy > 4.5:
        raise ValueError(
            "min_hydropathy must be between -4.5 and 4.5."
        )

    candidates = []

    for region in regions:
        length = region["length"]
        hydropathy = region["average_hydropathy"]

        length_matches = (
            min_length <= length <= max_length
        )

        hydropathy_matches = (
            hydropathy >= min_hydropathy
        )

        classification = (
            "candidate_transmembrane"
            if length_matches and hydropathy_matches
            else "hydrophobic_region"
        )

        candidates.append({
            **region,
            "length_matches": length_matches,
            "hydropathy_matches": hydropathy_matches,
            "classification": classification,
        })

    return candidates