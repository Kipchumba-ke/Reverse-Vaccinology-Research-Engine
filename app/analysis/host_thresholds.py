"""Thresholds used to interpret host-protein similarity.

These are screening conventions, not validated cutoffs, and no literature
source is claimed for the defaults. They exist in one place so they are
visible in reports and can be changed with environment variables:

    HOST_SIMILARITY_BROAD_IDENTITY     percent identity for "broad" or
                                       "partial" similarity (default 70)
    HOST_SIMILARITY_COVERAGE           percent coverage of query or host
                                       protein counted as "most of it"
                                       (default 80)
    HOST_SIMILARITY_MODERATE_IDENTITY  percent identity for "moderate"
                                       similarity (default 30)
    HOST_PEPTIDE_MIN_MATCH             shortest identical stretch, in
                                       residues, flagged in the short-
                                       peptide scan (default 8)
    HOST_PEPTIDE_MAX_QUERIES           most peptides searched per protein
                                       (default 25)
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class HostSimilarityThresholds:
    broad_identity: float = 70.0
    coverage: float = 80.0
    moderate_identity: float = 30.0
    peptide_min_match: int = 8
    peptide_max_queries: int = 25

    def describe(self) -> str:
        return (
            "Host-similarity interpretation uses provisional thresholds: "
            f"broad or partial similarity at {self.broad_identity:g}% "
            f"identity, {self.coverage:g}% coverage as \"most of the "
            f"protein\", moderate similarity from {self.moderate_identity:g}% "
            f"identity, and identical peptide matches of "
            f"{self.peptide_min_match} or more residues flagged. They are "
            "screening conventions, not validated cutoffs."
        )


def _read_number(name: str, default, low, high, cast):
    raw_value = os.environ.get(name)

    if raw_value is None or not raw_value.strip():
        return default

    try:
        value = cast(raw_value)
    except ValueError as error:
        raise RuntimeError(f"{name} must be a number.") from error

    if not low <= value <= high:
        raise RuntimeError(f"{name} must be between {low} and {high}.")

    return value


def load_host_similarity_thresholds() -> HostSimilarityThresholds:
    defaults = HostSimilarityThresholds()

    thresholds = HostSimilarityThresholds(
        broad_identity=_read_number(
            "HOST_SIMILARITY_BROAD_IDENTITY",
            defaults.broad_identity, 0, 100, float,
        ),
        coverage=_read_number(
            "HOST_SIMILARITY_COVERAGE",
            defaults.coverage, 0, 100, float,
        ),
        moderate_identity=_read_number(
            "HOST_SIMILARITY_MODERATE_IDENTITY",
            defaults.moderate_identity, 0, 100, float,
        ),
        peptide_min_match=_read_number(
            "HOST_PEPTIDE_MIN_MATCH",
            defaults.peptide_min_match, 4, 50, int,
        ),
        peptide_max_queries=_read_number(
            "HOST_PEPTIDE_MAX_QUERIES",
            defaults.peptide_max_queries, 1, 200, int,
        ),
    )

    if thresholds.moderate_identity > thresholds.broad_identity:
        raise RuntimeError(
            "HOST_SIMILARITY_MODERATE_IDENTITY cannot exceed "
            "HOST_SIMILARITY_BROAD_IDENTITY."
        )

    return thresholds
