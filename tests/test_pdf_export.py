import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from app.reporting.pdf_export import generate_report_pdf, summarise_prediction


requires_pdftotext = pytest.mark.skipif(
    shutil.which("pdftotext") is None,
    reason="pdftotext is not installed",
)


def pdf_text(report) -> str:
    with tempfile.TemporaryDirectory() as folder:
        pdf_path = Path(folder) / "report.pdf"
        text_path = Path(folder) / "report.txt"
        pdf_path.write_bytes(generate_report_pdf(report).getvalue())
        subprocess.run(
            ["pdftotext", str(pdf_path), str(text_path)],
            check=True,
            capture_output=True,
        )
        return text_path.read_text()


def sample_report(**overrides):
    report = {
        "metadata": {"report_type": "reverse_vaccinology"},
        "protein": {"id": "P0A911", "name": "Example protein", "length": 30},
        "measurements": {
            "sequence_predictions": {
                "deeptmhmm": {
                    "status": "completed",
                    "predicted_class": "TM",
                    "transmembrane_helices": 2,
                },
                "psortb": {
                    "status": "lookup_failed",
                    "message": "PSORTb did not finish in time.",
                },
            },
        },
        "prediction_status": {
            "deeptmhmm": {"status": "completed"},
            "psortb": {
                "status": "lookup_failed",
                "message": "PSORTb did not finish in time.",
            },
            "signalp": {
                "status": "not_configured",
                "message": "SignalP is not set up on this server.",
            },
        },
        "peptide_candidates": [
            {"start": 1, "end": 9, "length": 9, "sequence": "KKLLPTAAA"},
        ],
        "limitations": ["Illustrative test report."],
    }
    report.update(overrides)
    return report


def test_summarise_prediction_matches_the_web_report():
    assert summarise_prediction(
        "signalp", {"detected": False}
    ) == "No signal peptide predicted."
    assert summarise_prediction(
        "signalp",
        {
            "detected": True,
            "signal_peptide_type": "Sec/SPI",
            "cleavage_after": 22,
        },
    ) == "Sec/SPI; cleavage after residue 22."
    assert summarise_prediction(
        "deeptmhmm",
        {"predicted_class": "TM", "transmembrane_helices": 2},
    ) == "Class TM; 2 transmembrane helices."
    assert summarise_prediction(
        "psortb", {"localization": "Cytoplasmic", "score": 5}
    ) == "Cytoplasmic, score 5.00 of 10, below the 7.50 confidence cut-off."
    assert summarise_prediction(
        "epitopes",
        {
            "mhc_class_i": {"binders": [1, 2]},
            "mhc_class_ii": {"binders": []},
            "b_cell": {"regions": [1]},
        },
    ) == "2 MHC-I and 0 MHC-II binder windows; 1 B-cell regions."


def test_summarise_prediction_tolerates_odd_input():
    assert summarise_prediction("psortb", None) == ""
    assert summarise_prediction("psortb", {"localization": "X"}) == "X."
    assert summarise_prediction("unknown", {}) == ""


@requires_pdftotext
def test_pdf_lists_every_predictor_with_its_state():
    text = pdf_text(sample_report())

    assert "Prediction Tools" in text
    for name in ("SignalP 6.0", "DeepTMHMM", "PSORTb 3.0", "IEDB"):
        assert name in text

    assert "Not set up" in text
    assert "SignalP is not set up on this server." in text
    assert "Failed" in text
    assert "PSORTb did not finish in time." in text
    assert "Class TM; 2 transmembrane helices." in text
    # IEDB was not run, so it is reported as not enabled.
    assert "Not enabled on this server." in text


@requires_pdftotext
def test_pdf_omits_prediction_tools_for_older_reports():
    text = pdf_text(sample_report(measurements={}))

    assert "Prediction Tools" not in text
    assert "Protein Characteristics" in text


@requires_pdftotext
def test_pdf_follows_the_order_of_the_report_on_screen():
    text = pdf_text(sample_report())

    assert text.index("Protein Characteristics") < text.index(
        "Prediction Tools"
    )
    assert text.index("Limitations") < text.index("Peptide Candidates")
    # Sections carry the same numbered kickers as the web report.
    assert "01" in text and "02" in text


@requires_pdftotext
def test_pdf_does_not_repeat_raw_predictor_data():
    text = pdf_text(sample_report())

    assert "Deeptmhmm" not in text
    assert "Transmembrane Helices" not in text


def test_pdf_still_requires_a_report_object():
    with pytest.raises(ValueError):
        generate_report_pdf(None)


def test_pdf_builds_for_a_report_with_only_a_few_fields():
    pdf = generate_report_pdf({"limitations": ["Only a limitation."]})

    assert pdf.getvalue().startswith(b"%PDF-")
