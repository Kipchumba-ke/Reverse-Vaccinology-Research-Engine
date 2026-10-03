from app.models.analysis import Analysis


def test_analysis_stores_protein_metadata():
    analysis = Analysis(
        protein_id="sp|P12345|EXAMPLE",
        protein_name="Example protein",
        organism="Escherichia coli",
        accession="P12345",
        sequence="MKTAYIAKQRQISFVKSHFSRQ",
        status="completed",
    )

    assert analysis.protein_id == "sp|P12345|EXAMPLE"
    assert analysis.protein_name == "Example protein"
    assert analysis.organism == "Escherichia coli"
    assert analysis.accession == "P12345"
    assert analysis.sequence == "MKTAYIAKQRQISFVKSHFSRQ"
    assert analysis.status == "completed"

def test_analysis_has_an_id():
    analysis = Analysis()

    assert analysis.id is not None

def test_analysis_stores_analysis_report():
    report = {
        "sequence": "MKTAYIAKQRQISFVKSHFSRQ",
        "length": 22,
        "molecular_weight": 2500.0,
    }

    analysis = Analysis(
        sequence="MKTAYIAKQRQISFVKSHFSRQ",
        status="completed",
        report=report,
    )

    assert analysis.report == report