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

    assert result["status"] == "not_configured"
    assert "no psort executable was found" in result["message"]
    assert "PSORTB_BACKEND=docker" in result["message"]


def test_placeholder_executable_path_is_not_configured(monkeypatch):
    monkeypatch.setenv("PSORTB_EXECUTABLE", "/path/to/psort")

    result = psortb.fetch_psortb_prediction("MKKLLL")

    assert result["status"] == "not_configured"
    assert "/path/to/psort" in result["message"]


@pytest.fixture
def fake_psort(tmp_path, monkeypatch):
    executable = tmp_path / "psort"
    executable.write_text("#!/bin/sh\n")
    executable.chmod(0o755)
    monkeypatch.setenv("PSORTB_EXECUTABLE", str(executable))
    monkeypatch.delenv("PSORTB_BACKEND", raising=False)
    return str(executable)


def test_run_reads_the_results_directory(monkeypatch, fake_psort):
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


def test_run_falls_back_to_standard_output(monkeypatch, fake_psort):
    monkeypatch.setattr(
        psortb.subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            command, 0, "query\tCytoplasmic\t9.0\n", ""
        ),
    )

    assert psortb.fetch_psortb_prediction("MKK")["location"] == "cytoplasm"


def test_tool_failure_is_reported(monkeypatch, fake_psort):

    def failing(command, **kwargs):
        raise subprocess.CalledProcessError(1, command, stderr="boom")

    monkeypatch.setattr(psortb.subprocess, "run", failing)

    result = psortb.fetch_psortb_prediction("MKK")

    assert result["status"] == "lookup_failed"
    assert "boom" in result["message"]


# --- Docker backend ---------------------------------------------------------

@pytest.fixture
def fake_docker(tmp_path, monkeypatch):
    executable = tmp_path / "docker"
    executable.write_text("#!/bin/sh\n")
    executable.chmod(0o755)
    monkeypatch.setenv("PSORTB_BACKEND", "docker")
    monkeypatch.setenv("DOCKER_EXECUTABLE", str(executable))
    monkeypatch.delenv("PSORTB_DOCKER_IMAGE", raising=False)
    return str(executable)


def test_docker_backend_mounts_results_and_reads_the_report(
    monkeypatch, fake_docker
):
    seen = {}

    def fake_run(command, **kwargs):
        import os
        seen["command"] = command
        mount = command[command.index("-v") + 1]
        host_dir = mount.split(":")[0]
        # The input must be visible to the container in the mounted folder.
        seen["input_exists"] = os.path.isfile(f"{host_dir}/query.fasta")
        with open(f"{host_dir}/20260101_psortb_gram_neg.txt", "w") as handle:
            handle.write(HEADER + "query\tPeriplasmic\t8.8\n")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(psortb.subprocess, "run", fake_run)

    result = psortb.fetch_psortb_prediction("MKKLLL")
    command = seen["command"]

    assert result["status"] == "completed"
    assert result["location"] == "periplasm"
    assert result["backend"] == "docker"
    assert seen["input_exists"] is True
    assert command[1:3] == ["run", "--rm"]
    assert "brinkmanlab/psortb_commandline:1.0.2" in command
    assert command[command.index("-r") + 1] == "/tmp/results"
    assert command[command.index("-i") + 1] == "/tmp/results/query.fasta"
    assert "--negative" in command
    assert "-t" not in command and "-ti" not in command  # no TTY in a worker


def test_docker_image_and_gram_are_configurable(monkeypatch, fake_docker):
    monkeypatch.setenv("PSORTB_DOCKER_IMAGE", "example/psortb:9")
    monkeypatch.setenv("PSORTB_GRAM", "positive")
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        return subprocess.CompletedProcess(
            command, 0, "query\tCellwall\t9.1\n", ""
        )

    monkeypatch.setattr(psortb.subprocess, "run", fake_run)

    result = psortb.fetch_psortb_prediction("MKK")

    assert result["gram"] == "positive"
    assert "example/psortb:9" in seen["command"]
    assert "--positive" in seen["command"]


def test_missing_docker_is_not_configured(monkeypatch):
    monkeypatch.setenv("PSORTB_BACKEND", "docker")
    monkeypatch.setenv("DOCKER_EXECUTABLE", "/no/such/docker")

    result = psortb.fetch_psortb_prediction("MKK")

    assert result["status"] == "not_configured"
    assert "docker command was not found" in result["message"]


def test_docker_failure_is_reported(monkeypatch, fake_docker):
    def failing(command, **kwargs):
        raise subprocess.CalledProcessError(
            125, command, stderr="Cannot connect to the Docker daemon"
        )

    monkeypatch.setattr(psortb.subprocess, "run", failing)

    result = psortb.fetch_psortb_prediction("MKK")

    assert result["status"] == "lookup_failed"
    assert "Docker daemon" in result["message"]


def test_unknown_backend_is_reported(monkeypatch):
    monkeypatch.setenv("PSORTB_BACKEND", "cloud")

    result = psortb.fetch_psortb_prediction("MKK")

    assert result["status"] == "lookup_failed"
    assert "PSORTB_BACKEND" in result["message"]
