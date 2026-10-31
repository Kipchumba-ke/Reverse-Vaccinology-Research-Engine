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


# --- BioLib backend -------------------------------------------------------

class _FakeJob:
    def __init__(self, results_text):
        self._results_text = results_text

    def save_files(self, output_dir):
        import os
        nested = os.path.join(output_dir, "output")
        os.makedirs(nested)
        if self._results_text is not None:
            with open(os.path.join(nested, "prediction_results.txt"), "w") as f:
                f.write(self._results_text)


def _install_fake_biolib(monkeypatch, results_text, calls, raises=None):
    import sys
    import types

    class _App:
        def cli(self, args, blocking):
            if raises:
                raise raises
            import os
            calls["args"] = args
            calls["blocking"] = blocking
            calls["input"] = open("input.fasta").read()
            calls["cwd_during_run"] = os.getcwd()
            return _FakeJob(results_text)

    module = types.ModuleType("biolib")

    def load(name):
        calls["app"] = name
        return _App()

    module.load = load
    monkeypatch.setitem(sys.modules, "biolib", module)


def test_biolib_backend_runs_the_app_and_parses_results(monkeypatch):
    import os
    monkeypatch.setenv("SIGNALP_BACKEND", "biolib")
    monkeypatch.delenv("SIGNALP_BIOLIB_APP", raising=False)
    monkeypatch.delenv("SIGNALP_ORGANISM", raising=False)
    calls = {}
    _install_fake_biolib(monkeypatch, HEADER + SP_ROW, calls)
    before = os.getcwd()

    result = signalp.fetch_signalp_prediction("MKKLLLLLAAA")

    assert result["status"] == "completed"
    assert result["detected"] is True
    assert result["cleavage_after"] == 22
    assert calls["app"] == "DTU/SignalP_6"
    assert "--fastafile input.fasta" in calls["args"]
    assert "--organism other" in calls["args"]
    assert "--output_dir output" in calls["args"]
    assert calls["blocking"] is True
    assert calls["input"] == ">query\nMKKLLLLLAAA\n"
    assert os.getcwd() == before  # working directory restored


def test_biolib_app_name_and_organism_are_configurable(monkeypatch):
    monkeypatch.setenv("SIGNALP_BACKEND", "biolib")
    monkeypatch.setenv("SIGNALP_BIOLIB_APP", "DTU/SignalP-6")
    monkeypatch.setenv("SIGNALP_ORGANISM", "eukarya")
    calls = {}
    _install_fake_biolib(monkeypatch, HEADER + OTHER_ROW, calls)

    result = signalp.fetch_signalp_prediction("MKKLLLLLAAA")

    assert result["status"] == "completed"
    assert result["detected"] is False
    assert calls["app"] == "DTU/SignalP-6"
    assert "--organism eukarya" in calls["args"]


def test_biolib_backend_does_not_call_the_local_executable(monkeypatch):
    monkeypatch.setenv("SIGNALP_BACKEND", "biolib")
    monkeypatch.setattr(
        signalp.subprocess, "run",
        lambda *a, **k: pytest.fail("local signalp6 must not run"),
    )
    _install_fake_biolib(monkeypatch, HEADER + SP_ROW, {})

    assert signalp.fetch_signalp_prediction("MKKLLLLL")["status"] == "completed"


def test_missing_pybiolib_is_reported(monkeypatch):
    import sys
    monkeypatch.setenv("SIGNALP_BACKEND", "biolib")
    monkeypatch.setitem(sys.modules, "biolib", None)  # makes import fail

    result = signalp.fetch_signalp_prediction("MKKLLLLL")

    assert result["status"] == "lookup_failed"
    assert "pip install pybiolib" in result["message"]


def test_biolib_failure_is_reported_and_cwd_restored(monkeypatch):
    import os
    monkeypatch.setenv("SIGNALP_BACKEND", "biolib")
    _install_fake_biolib(monkeypatch, None, {}, raises=Exception("quota exceeded"))
    before = os.getcwd()

    result = signalp.fetch_signalp_prediction("MKKLLLLL")

    assert result["status"] == "lookup_failed"
    assert "quota exceeded" in result["message"]
    assert os.getcwd() == before


def test_biolib_run_without_results_file_is_reported(monkeypatch):
    monkeypatch.setenv("SIGNALP_BACKEND", "biolib")
    _install_fake_biolib(monkeypatch, None, {})

    result = signalp.fetch_signalp_prediction("MKKLLLLL")

    assert result["status"] == "lookup_failed"
    assert "no prediction_results.txt" in result["message"]


def test_unknown_backend_is_reported(monkeypatch):
    monkeypatch.setenv("SIGNALP_BACKEND", "cloud")

    result = signalp.fetch_signalp_prediction("MKKLLLLL")

    assert result["status"] == "lookup_failed"
    assert "SIGNALP_BACKEND" in result["message"]


def test_local_is_the_default_backend(monkeypatch):
    monkeypatch.delenv("SIGNALP_BACKEND", raising=False)

    assert signalp._resolve_backend() == "local"
