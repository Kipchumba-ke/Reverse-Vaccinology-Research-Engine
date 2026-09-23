from app.services.analysis_service import analyze_sequence


def test_analyze_sequence_returns_protein_report():
    sequence = "MKTAYIAKQRQISFVKSHFSRQ"

    report = analyze_sequence(sequence)

    assert "protein" in report
    assert "measurements" in report
    assert "evidence" in report
    assert "interpretations" in report
    assert "candidate_assessment" in report
    assert "limitations" in report
    assert "conservation" in report
    assert "metadata" in report

def test_analyze_sequence_preserves_protein_metadata():
    report = analyze_sequence(
        "MKTAYIAKQRQISFVKSHFSRQ",
        protein_id="sp|P12345|EXAMPLE",
        protein_name="Example protein",
        organism="Escherichia coli",
        accession="P12345",
    )

    assert report["protein"]["id"] == "sp|P12345|EXAMPLE"
    assert report["protein"]["name"] == "Example protein"
    assert report["protein"]["organism"] == "Escherichia coli"
    assert report["protein"]["accession"] == "P12345"