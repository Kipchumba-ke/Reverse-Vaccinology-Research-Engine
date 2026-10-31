from app.analysis.pipeline import analyze_protein
from app.reporting.report import generate_protein_report
from app.services import prediction_service
from app.integrations import deeptmhmm, psortb, signalp

SEQ = "MKKRLLLALLLALVLAAVSAQADEKSTNQDEKSTNQDEKSTNQ"


def fresh():
    return analyze_protein(SEQ)


def test_nothing_runs_by_default(monkeypatch):
    for name in ("SIGNALP_ENABLED", "DEEPTMHMM_ENABLED", "PSORTB_ENABLED"):
        monkeypatch.delenv(name, raising=False)

    result = fresh()

    assert prediction_service.attach_predictions(result) == {}
    assert result.localization_evidence == []


def test_enabled_predictors_add_evidence_and_status(monkeypatch):
    monkeypatch.setenv("DEEPTMHMM_ENABLED", "1")
    monkeypatch.setenv("PSORTB_ENABLED", "1")
    monkeypatch.delenv("SIGNALP_ENABLED", raising=False)

    tm = deeptmhmm.parse_three_line(
        ">query | TM\n" + SEQ + "\n"
        + "I" * 5 + "M" * 20 + "O" * (len(SEQ) - 25) + "\n"
    )
    monkeypatch.setattr(
        deeptmhmm, "fetch_deeptmhmm_prediction",
        lambda sequence: {"status": "completed", **tm},
    )
    monkeypatch.setattr(
        psortb, "fetch_psortb_prediction",
        lambda sequence: {
            "status": "completed", "gram": "negative",
            **psortb.parse_terse_output("q\tCytoplasmicMembrane\t9.8\n"),
        },
    )

    result = fresh()
    status = prediction_service.attach_predictions(result)

    assert set(status) == {"deeptmhmm", "psortb"}
    assert {e.source for e in result.localization_evidence} == {
        "DeepTMHMM", "PSORTb 3.0",
    }
    assert set(result.sequence_predictions) >= {"deeptmhmm", "psortb"}


def test_agreeing_predictors_are_reported_as_supporting(monkeypatch):
    monkeypatch.setenv("DEEPTMHMM_ENABLED", "1")
    monkeypatch.setenv("PSORTB_ENABLED", "1")
    monkeypatch.delenv("SIGNALP_ENABLED", raising=False)
    tm = deeptmhmm.parse_three_line(
        ">query | TM\n" + SEQ + "\n"
        + "I" * 5 + "M" * 20 + "O" * (len(SEQ) - 25) + "\n"
    )
    monkeypatch.setattr(
        deeptmhmm, "fetch_deeptmhmm_prediction",
        lambda sequence: {"status": "completed", **tm},
    )
    monkeypatch.setattr(
        psortb, "fetch_psortb_prediction",
        lambda sequence: {
            "status": "completed", "gram": "negative",
            **psortb.parse_terse_output("q\tCytoplasmicMembrane\t9.8\n"),
        },
    )

    result = fresh()
    prediction_service.attach_predictions(result)
    report = generate_protein_report(result)

    supporting = report["candidate_assessment"]["supporting_evidence"]
    assert any("agree on the same location" in line for line in supporting)
    assert report["evidence"]["localization"]


def test_failures_are_recorded_and_do_not_add_evidence(monkeypatch):
    monkeypatch.setenv("PSORTB_ENABLED", "1")
    monkeypatch.delenv("DEEPTMHMM_ENABLED", raising=False)
    monkeypatch.delenv("SIGNALP_ENABLED", raising=False)
    monkeypatch.setattr(
        psortb, "fetch_psortb_prediction",
        lambda sequence: {
            "status": "lookup_failed", "method": "PSORTb 3.0",
            "message": "psort executable not found.",
        },
    )

    result = fresh()
    status = prediction_service.attach_predictions(result)

    assert status["psortb"]["status"] == "lookup_failed"
    assert result.localization_evidence == []
    assert result.sequence_predictions["psortb"]["status"] == "lookup_failed"


def test_signalp_still_attaches_when_enabled(monkeypatch):
    monkeypatch.setenv("SIGNALP_ENABLED", "1")
    monkeypatch.delenv("DEEPTMHMM_ENABLED", raising=False)
    monkeypatch.delenv("PSORTB_ENABLED", raising=False)
    monkeypatch.setattr(
        signalp, "fetch_signalp_prediction",
        lambda sequence: {"status": "completed", "detected": True},
    )

    result = fresh()
    status = prediction_service.attach_predictions(result)

    assert status == {"signalp": {"status": "completed", "message": None}}
    assert result.sequence_predictions["signalp"]["detected"] is True


def test_iedb_results_annotate_peptide_windows(monkeypatch):
    from app.integrations import iedb

    monkeypatch.setenv("IEDB_ENABLED", "1")
    for name in ("SIGNALP_ENABLED", "DEEPTMHMM_ENABLED", "PSORTB_ENABLED"):
        monkeypatch.delenv(name, raising=False)

    prediction = {
        "status": "completed",
        "method": "IEDB Analysis Resource",
        "mhc_class_i": {"binders": [{
            "start": 3, "end": 11,
            "alleles": [{"allele": "HLA-A*02:01"}],
        }]},
        "mhc_class_ii": {"binders": []},
        "b_cell": {"regions": [{"start": 5, "end": 12}]},
    }
    monkeypatch.setattr(
        iedb, "fetch_epitope_predictions", lambda sequence: prediction
    )

    result = fresh()
    status = prediction_service.attach_predictions(result)

    assert status["iedb"]["status"] == "completed"
    first = result.peptide_candidates[0]
    assert first["overlaps_b_cell_epitope"] is True
    assert first["mhc_i_binder_alleles"] == 1
    report = generate_protein_report(result)
    assert any("IEDB" in line for line in report["limitations"])


def test_iedb_failure_leaves_windows_unchanged(monkeypatch):
    from app.integrations import iedb

    monkeypatch.setenv("IEDB_ENABLED", "1")
    for name in ("SIGNALP_ENABLED", "DEEPTMHMM_ENABLED", "PSORTB_ENABLED"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(
        iedb, "fetch_epitope_predictions",
        lambda sequence: {"status": "lookup_failed", "message": "down"},
    )

    result = fresh()
    before = [dict(p) for p in result.peptide_candidates]
    status = prediction_service.attach_predictions(result)

    assert status["iedb"]["status"] == "lookup_failed"
    assert result.peptide_candidates == before


def test_not_configured_is_recorded_as_its_own_status(monkeypatch):
    monkeypatch.setenv("SIGNALP_ENABLED", "1")
    monkeypatch.setenv("SIGNALP_BACKEND", "local")
    monkeypatch.setenv("SIGNALP6_EXECUTABLE", "/path/to/signalp6")
    monkeypatch.delenv("DEEPTMHMM_ENABLED", raising=False)
    monkeypatch.delenv("PSORTB_ENABLED", raising=False)
    monkeypatch.delenv("IEDB_ENABLED", raising=False)

    result = fresh()
    status = prediction_service.attach_predictions(result)

    assert status["signalp"]["status"] == "not_configured"
    assert "SIGNALP6_EXECUTABLE" in status["signalp"]["message"] or \
        "signalp6" in status["signalp"]["message"]
    assert result.sequence_predictions["signalp"]["status"] == "not_configured"
    assert result.localization_evidence == []
