import subprocess

import pytest

from app.integrations import signalp

HEADER = (
    "# SignalP-6.0\tOrganism: Other\tTimestamp: 20260101000000\n"
    "# ID\tPrediction\tOTHER\tSP(Sec/SPI)\tLIPO(Sec/SPII)\t"
    "TAT(Tat/SPI)\tTATLIPO(Tat/SPII)\tPILIN(Sec/SPIII)\tCS Position\n"
)
SP_ROW = (
    "query\tSP\t0.0006\t0.9993\t0.0000\t0.0000\t0.0000\t0.0000\t"
    "CS pos: 22-23. Pr: 0.9831\n"
)
OTHER_ROW = (
    "query\tOTHER\t0.9998\t0.0002\t0.0000\t0.0000\t0.0000\t0.0000\t\n"
)


def test_signal_peptide_row_is_parsed():
    result = signalp.parse_signalp_prediction(HEADER + SP_ROW)

    assert result["detected"] is True
    assert result["prediction"] == "SP"
    assert result["cleavage_after"] == 22
    assert result["cleavage_probability"] == pytest.approx(0.9831)
    assert result["method"] == "SignalP 6.0"


def test_no_signal_peptide_row_is_parsed():
    result = signalp.parse_signalp_prediction(HEADER + OTHER_ROW)

    assert result["detected"] is False


def test_lipoprotein_label_is_described():
    row = SP_ROW.replace("\tSP\t", "\tLIPO\t")

    result = signalp.parse_signalp_prediction(HEADER + row)

    assert "lipoprotein" in result["signal_peptide_type"]


@pytest.mark.parametrize("text", [
    HEADER,
    HEADER + SP_ROW + SP_ROW,
    HEADER + "query\tBOGUS\t0\t0\t0\t0\t0\t0\t\n",
    HEADER + "query\n",
])
def test_unexpected_output_is_rejected(text):
    with pytest.raises(ValueError):
        signalp.parse_signalp_prediction(text)


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SIGNALP_ENABLED", raising=False)

    assert signalp.is_signalp_enabled() is False


def test_invalid_organism_is_rejected():
    with pytest.raises(ValueError):
        signalp.run_signalp("MKK", organism="bacteria")


def test_missing_executable_is_reported(monkeypatch):
    monkeypatch.delenv("SIGNALP6_EXECUTABLE", raising=False)
    monkeypatch.setattr(signalp.shutil, "which", lambda name: None)

    result = signalp.fetch_signalp_prediction("MKKLLLLL")

    assert result["status"] == "lookup_failed"
    assert "not found" in result["message"]


def test_run_reads_results_written_by_the_tool(monkeypatch):
    monkeypatch.setenv("SIGNALP6_EXECUTABLE", "/usr/bin/signalp6")
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        out = command[command.index("--output_dir") + 1]
        import os
        os.makedirs(out)
        with open(os.path.join(out, "prediction_results.txt"), "w") as f:
            f.write(HEADER + SP_ROW)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(signalp.subprocess, "run", fake_run)

    result = signalp.fetch_signalp_prediction("MKKLLLLL")

    assert result["status"] == "completed"
    assert result["cleavage_after"] == 22
    assert "--organism" in captured["command"]


def test_tool_failure_is_reported(monkeypatch):
    monkeypatch.setenv("SIGNALP6_EXECUTABLE", "/usr/bin/signalp6")

    def failing(command, **kwargs):
        raise subprocess.CalledProcessError(1, command, stderr="boom")

    monkeypatch.setattr(signalp.subprocess, "run", failing)

    result = signalp.fetch_signalp_prediction("MKKLLLLL")

    assert result["status"] == "lookup_failed"
    assert "boom" in result["message"]
