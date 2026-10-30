import pytest

from app.analysis.blast_runner import (
    SHORT_PEPTIDE_OUTFMT,
    build_blastp_short_command,
)
from app.analysis.host_peptide_scan import (
    build_peptide_fasta,
    is_peptide_scan_enabled,
    parse_peptide_hits,
    scan_peptides_against_host,
    select_peptides_for_scan,
)
from app.analysis.host_thresholds import (
    HostSimilarityThresholds,
    load_host_similarity_thresholds,
)

THRESHOLDS = HostSimilarityThresholds()


def peptide(start, sequence="ACDEFGHIKLMNPQR", **extra):
    return {
        "start": start,
        "end": start + len(sequence) - 1,
        "sequence": sequence,
        "mean_antigenic_propensity": 1.0,
        "overlaps_antigenic_region": False,
        "overlaps_transmembrane": False,
        **extra,
    }


def line(query, subject, pident, length, qs=1, qe=15, ss=10, se=24):
    return "\t".join(map(str, [
        query, subject, pident, length, 15, 400, "0.5", qs, qe, ss, se,
    ]))


def test_defaults_match_the_previous_hardcoded_values():
    thresholds = load_host_similarity_thresholds()

    assert thresholds.broad_identity == 70
    assert thresholds.coverage == 80
    assert thresholds.moderate_identity == 30


def test_thresholds_can_be_overridden(monkeypatch):
    monkeypatch.setenv("HOST_SIMILARITY_BROAD_IDENTITY", "90")
    monkeypatch.setenv("HOST_PEPTIDE_MIN_MATCH", "6")

    thresholds = load_host_similarity_thresholds()

    assert thresholds.broad_identity == 90
    assert thresholds.peptide_min_match == 6


@pytest.mark.parametrize("name,value", [
    ("HOST_SIMILARITY_BROAD_IDENTITY", "abc"),
    ("HOST_SIMILARITY_COVERAGE", "150"),
    ("HOST_PEPTIDE_MIN_MATCH", "1"),
])
def test_invalid_threshold_values_are_rejected(monkeypatch, name, value):
    monkeypatch.setenv(name, value)

    with pytest.raises(RuntimeError, match=name):
        load_host_similarity_thresholds()


def test_moderate_threshold_cannot_exceed_broad(monkeypatch):
    monkeypatch.setenv("HOST_SIMILARITY_MODERATE_IDENTITY", "80")

    with pytest.raises(RuntimeError):
        load_host_similarity_thresholds()


def test_description_states_the_values_and_that_they_are_not_validated():
    text = THRESHOLDS.describe()

    assert "70%" in text and "80%" in text
    assert "not validated" in text


def test_scan_is_off_unless_enabled(monkeypatch):
    monkeypatch.delenv("HOST_PEPTIDE_SCAN", raising=False)
    assert is_peptide_scan_enabled() is False

    monkeypatch.setenv("HOST_PEPTIDE_SCAN", "1")
    assert is_peptide_scan_enabled() is True


def test_selection_prefers_antigenic_non_membrane_windows():
    peptides = [
        peptide(1),
        peptide(2, overlaps_antigenic_region=True, overlaps_transmembrane=True),
        peptide(3, overlaps_antigenic_region=True, mean_antigenic_propensity=1.2),
        peptide(4, overlaps_antigenic_region=True, mean_antigenic_propensity=1.4),
    ]

    chosen = select_peptides_for_scan(peptides, 3)

    assert [p["start"] for p in chosen] == [4, 3, 2]


def test_selection_requires_a_positive_limit():
    with pytest.raises(ValueError):
        select_peptides_for_scan([peptide(1)], 0)


def test_fasta_uses_position_based_ids():
    assert build_peptide_fasta([peptide(5)]) == (
        ">pep_5_19\nACDEFGHIKLMNPQR\n"
    )


def test_command_uses_short_query_settings():
    command = build_blastp_short_command("blastp", "/db/human")

    assert command[command.index("-task") + 1] == "blastp-short"
    assert command[command.index("-matrix") + 1] == "PAM30"
    assert command[command.index("-word_size") + 1] == "2"
    assert command[command.index("-evalue") + 1] == "20000"
    assert command[command.index("-db") + 1] == "/db/human"
    assert command[-1] == SHORT_PEPTIDE_OUTFMT


def test_hits_below_minimum_identical_residues_are_dropped():
    peptides = [peptide(1)]
    output = "\n".join([
        line("pep_1_15", "sp|A|X", 100.0, 7),
        line("pep_1_15", "sp|B|Y", 100.0, 9),
    ])

    hits = parse_peptide_hits(output, peptides, THRESHOLDS)

    assert [h["host_id"] for h in hits] == ["sp|B|Y"]
    assert hits[0]["exact_match"] is True
    assert hits[0]["identical_residues"] == 9


def test_near_matches_report_exact_match_false():
    hits = parse_peptide_hits(
        line("pep_1_15", "sp|B|Y", 80.0, 12),
        [peptide(1)],
        THRESHOLDS,
    )

    assert hits[0]["identical_residues"] == 10
    assert hits[0]["exact_match"] is False


def test_unknown_query_ids_are_ignored_and_bad_rows_rejected():
    assert parse_peptide_hits(
        line("other", "sp|B|Y", 100.0, 12), [peptide(1)], THRESHOLDS
    ) == []

    with pytest.raises(ValueError):
        parse_peptide_hits("a\tb\tc", [peptide(1)], THRESHOLDS)


def test_scan_reports_matches():
    runner = lambda fasta, db: line("pep_1_15", "sp|B|Y", 100.0, 10)

    result = scan_peptides_against_host(
        [peptide(1)], "/db/human", THRESHOLDS, runner=runner
    )

    assert result["status"] == "matches_found"
    assert result["peptides_with_matches"] == 1
    assert result["matches"][0]["host_id"] == "sp|B|Y"


def test_scan_without_matches_does_not_claim_safety():
    result = scan_peptides_against_host(
        [peptide(1)], "/db/human", THRESHOLDS, runner=lambda f, d: ""
    )

    assert result["status"] == "no_matches"
    assert "does not show" in result["message"]


def test_scan_failure_is_reported_not_raised():
    def failing(fasta, database):
        raise RuntimeError("blastp executable not found.")

    result = scan_peptides_against_host(
        [peptide(1)], "/db/human", THRESHOLDS, runner=failing
    )

    assert result["status"] == "lookup_failed"
    assert "blastp" in result["message"]


def test_scan_with_no_peptides_is_not_performed():
    result = scan_peptides_against_host([], "/db/human", THRESHOLDS)

    assert result["status"] == "not_performed"


def test_only_the_configured_number_of_peptides_is_searched():
    thresholds = HostSimilarityThresholds(peptide_max_queries=2)
    seen = {}

    def runner(fasta, database):
        seen["records"] = fasta.count(">")
        return ""

    scan_peptides_against_host(
        [peptide(i) for i in range(1, 6)], "/db", thresholds, runner=runner
    )

    assert seen["records"] == 2
