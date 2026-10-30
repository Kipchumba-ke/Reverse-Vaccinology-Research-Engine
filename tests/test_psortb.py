import subprocess

import pytest

from app.integrations import psortb

HEADER = "SeqID\tLocalization\tScore\n"


def test_terse_row_is_parsed():
    result = psortb.parse_terse_output(
        HEADER + "query\tCytoplasmicMembrane\t9.82\n"
    )

    assert result["localization"] == "CytoplasmicMembrane"
    assert result["location"] == "inner_membrane"
    assert result["score"] == 9.82


def test_header_is_optional():
    result = psortb.parse_terse_output("query\tUnknown\t7.0\n")

    assert result["location"] == "unknown"


@pytest.mark.parametrize("text", [
    "",
    HEADER,
    HEADER + "query\tCytoplasmic\t9.0\nother\tCytoplasmic\t9.0\n",
    HEADER + "query\tNowhere\t9.0\n",
    HEADER + "query\tCytoplasmic\n",
])
def test_unexpected_output_is_rejected(text):
    with pytest.raises(ValueError):
        psortb.parse_terse_output(text)


@pytest.mark.parametrize("category,expected", [
    ("Cytoplasmic", "cytoplasm"),
    ("Periplasmic", "periplasm"),
    ("OuterMembrane", "outer_membrane"),
    ("Extracellular", "extracellular"),
    ("Cellwall", "extracellular"),
])
def test_categories_map_to_known_locations(category, expected):
    prediction = psortb.parse_terse_output(f"query\t{category}\t9.5\n")

    assert prediction["location"] == expected


def test_confident_score_gives_medium_confidence():
    prediction = psortb.parse_terse_output("query\tPeriplasmic\t9.5\n")

    evidence = psortb.to_localization_evidence(prediction, "negative")

    assert evidence[0].confidence == "medium"
    assert evidence[0].source == "PSORTb 3.0"


def test_low_score_gives_low_confidence_and_says_why():
    prediction = psortb.parse_terse_output("query\tPeriplasmic\t5.0\n")

    evidence = psortb.to_localization_evidence(prediction, "negative")

    assert evidence[0].confidence == "low"
    assert "below" in evidence[0].description


def test_unknown_is_kept_as_unknown_evidence():
    prediction = psortb.parse_terse_output("query\tUnknown\t2.0\n")

    evidence = psortb.to_localization_evidence(prediction, "negative")

    assert evidence[0].location == "unknown"


def test_invalid_gram_is_rejected():
    with pytest.raises(ValueError):
        psortb.run_psortb("MKK", gram="bacteria")


def test_missing_executable_is_reported(monkeypatch):
    monkeypatch.delenv("PSORTB_EXECUTABLE", raising=False)
    monkeypatch.setattr(psortb.shutil, "which", lambda name: None)

    result = psortb.fetch_psortb_prediction("MKKLLL")

    assert result["status"] == "lookup_failed"
    assert "not found" in result["message"]


def test_run_reads_the_results_directory(monkeypatch):
    monkeypatch.setenv("PSORTB_EXECUTABLE", "/usr/bin/psort")
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        results = command[command.index("-r") + 1]
        with open(f"{results}/20260101_psortb_terse.txt", "w") as handle:
            handle.write(HEADER + "query\tOuterMembrane\t9.9\n")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(psortb.subprocess, "run", fake_run)

    result = psortb.fetch_psortb_prediction("MKKLLL")

    assert result["status"] == "completed"
    assert result["location"] == "outer_membrane"
    assert result["gram"] == "negative"
    assert "--negative" in seen["command"]


def test_run_falls_back_to_standard_output(monkeypatch):
    monkeypatch.setenv("PSORTB_EXECUTABLE", "/usr/bin/psort")
    monkeypatch.setattr(
        psortb.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            command, 0, "query\tCytoplasmic\t9.0\n", ""
        ),
    )

    assert psortb.fetch_psortb_prediction("MKK")["location"] == "cytoplasm"


def test_tool_failure_is_reported(monkeypatch):
    monkeypatch.setenv("PSORTB_EXECUTABLE", "/usr/bin/psort")

    def failing(command, **kwargs):
        raise subprocess.CalledProcessError(1, command, stderr="boom")

    monkeypatch.setattr(psortb.subprocess, "run", failing)

    result = psortb.fetch_psortb_prediction("MKK")

    assert result["status"] == "lookup_failed"
    assert "boom" in result["message"]
