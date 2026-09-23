from app.services.analysis_service import (
    analyze_sequence,
    analyze_fasta_records,
)


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

def test_analyze_fasta_records_with_single_record_returns_report():
    records = [
        {
            "id": "sp|P12345|EXAMPLE",
            "description": "Example protein",
            "organism": "Escherichia coli",
            "accession": "P12345",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        }
    ]

    report = analyze_fasta_records(records)

    assert report["protein"]["id"] == "sp|P12345|EXAMPLE"
    assert report["protein"]["name"] == "Example protein"
    assert report["protein"]["organism"] == "Escherichia coli"
    assert report["protein"]["accession"] == "P12345"

def test_analyze_fasta_records_with_multiple_records_returns_workflow_dict():
    records = [
        {
            "id": "sp|P12345|EXAMPLE1",
            "description": "Example protein 1",
            "organism": "Escherichia coli",
            "accession": "P12345",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        },
        {
            "id": "sp|P67890|EXAMPLE2",
            "description": "Example protein 2",
            "organism": "Escherichia coli",
            "accession": "P67890",
            "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        },
    ]

    result = analyze_fasta_records(records)

    assert result["records"] == records
    assert len(result["protein_analyses"]) == 2
    assert result["alignment"] is not None
    assert result["conservation"] is not None
