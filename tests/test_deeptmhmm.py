import pytest

from app.integrations import deeptmhmm

SEQ = "MKKLLPLAAAVLLLLGAGSDEKQRTNDEKS"


def three_line(predicted_class, labels, sequence=SEQ):
    return f">query | {predicted_class}\n{sequence}\n{labels}\n"


def test_label_runs_become_one_based_segments():
    segments = deeptmhmm.parse_label_segments("SSSOOMMMMOOBBBII")

    assert segments == [
        {"type": "signal_peptide", "start": 1, "end": 3},
        {"type": "transmembrane_helix", "start": 6, "end": 9},
        {"type": "beta_strand", "start": 12, "end": 14},
    ]


def test_transmembrane_protein_is_parsed():
    labels = "I" * 5 + "M" * 20 + "O" * 5
    result = deeptmhmm.parse_three_line(three_line("TM", labels))

    assert result["predicted_class"] == "TM"
    assert result["transmembrane_helices"] == 1
    assert result["segments"][0]["start"] == 6
    assert result["segments"][0]["end"] == 25


def test_globular_protein_has_no_segments():
    result = deeptmhmm.parse_three_line(
        three_line("GLOBULAR", "I" * len(SEQ))
    )

    assert result["segments"] == []


@pytest.mark.parametrize("text", [
    "",
    ">query | TM\nMKK\n",
    ">query | TM\nMKK\nIII\nextra\n",
    ">query | TM\nMKKK\nIII\n",
    ">query | WEIRD\nMKK\nIII\n",
])
def test_unexpected_output_is_rejected(text):
    with pytest.raises(ValueError):
        deeptmhmm.parse_three_line(text)


def test_helical_membrane_protein_gives_inner_membrane_evidence():
    labels = "I" * 5 + "M" * 20 + "O" * 5
    prediction = deeptmhmm.parse_three_line(three_line("TM", labels))

    evidence = deeptmhmm.to_localization_evidence(prediction)

    assert [e.location for e in evidence] == ["inner_membrane"]
    assert evidence[0].source == "DeepTMHMM"
    assert "Gram-negative" in evidence[0].description


def test_beta_barrel_gives_outer_membrane_evidence():
    prediction = deeptmhmm.parse_three_line(
        three_line("BETA", "O" * 10 + "B" * 10 + "I" * 10)
    )

    evidence = deeptmhmm.to_localization_evidence(prediction)

    assert [e.location for e in evidence] == ["outer_membrane"]


@pytest.mark.parametrize("predicted_class", ["SP", "GLOBULAR"])
def test_classes_without_a_compartment_give_no_evidence(predicted_class):
    prediction = deeptmhmm.parse_three_line(
        three_line(predicted_class, "S" * 10 + "O" * 20)
    )

    assert deeptmhmm.to_localization_evidence(prediction) == []


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("DEEPTMHMM_ENABLED", raising=False)

    assert deeptmhmm.is_deeptmhmm_enabled() is False


def test_missing_biolib_is_reported(monkeypatch):
    import builtins

    real_import = builtins.__import__

    def blocked(name, *args, **kwargs):
        if name == "biolib":
            raise ImportError("no biolib")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked)

    result = deeptmhmm.fetch_deeptmhmm_prediction(SEQ)

    assert result["status"] == "not_configured"
    assert "pybiolib" in result["message"]


def test_biolib_run_is_parsed_and_uses_the_app_arguments(monkeypatch):
    import os
    import sys
    import types

    calls = {}
    labels = "I" * 5 + "M" * 20 + "O" * 5

    class _Job:
        def save_files(self, output_dir):
            os.makedirs(os.path.join(output_dir, "nested"))
            path = os.path.join(output_dir, "nested", "predicted_topologies.3line")
            with open(path, "w") as handle:
                handle.write(three_line("TM", labels))

    class _App:
        def cli(self, args, blocking):
            calls["args"] = args
            calls["blocking"] = blocking
            calls["input"] = open("input.fasta").read()
            return _Job()

    module = types.ModuleType("biolib")
    module.load = lambda name: calls.setdefault("app", name) and _App()
    monkeypatch.setitem(sys.modules, "biolib", module)
    before = os.getcwd()

    result = deeptmhmm.fetch_deeptmhmm_prediction(SEQ)

    assert result["status"] == "completed"
    assert result["predicted_class"] == "TM"
    assert calls["app"] == "DTU/DeepTMHMM"
    assert calls["args"] == "--fasta input.fasta"
    assert calls["blocking"] is True
    assert calls["input"] == f">query\n{SEQ}\n"
    assert os.getcwd() == before


def test_biolib_failure_is_a_lookup_failure(monkeypatch):
    import sys
    import types

    class _App:
        def cli(self, args, blocking):
            raise Exception("not signed in")

    module = types.ModuleType("biolib")
    module.load = lambda name: _App()
    monkeypatch.setitem(sys.modules, "biolib", module)

    result = deeptmhmm.fetch_deeptmhmm_prediction(SEQ)

    assert result["status"] == "lookup_failed"
    assert "not signed in" in result["message"]
