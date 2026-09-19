from app.input.fasta import analyze_fasta_file


def test_analyze_fasta_file_runs_protein_analysis(tmp_path):
    fasta_file = tmp_path / "protein.fasta"

    fasta_file.write_text(
        ">protein_1\n"
        "MKTIIALSYIFCLVFAD\n"
    )

    result = analyze_fasta_file(fasta_file)

    assert result.sequence == "MKTIIALSYIFCLVFAD"
    assert result.length == 17
    assert result.molecular_weight > 0
    assert isinstance(result.gravy, float)

def test_analyze_fasta_file_runs_protein_analysis(tmp_path):
    fasta_file = tmp_path / "protein.fasta"
    fasta_file.write_text(
        ">protein_1\n"
        "MKTIIALSYIFCLVFAD\n"
    )

    result = analyze_fasta_file(fasta_file)

    assert result.sequence == "MKTIIALSYIFCLVFAD"
    assert result.length == 17
    assert result.molecular_weight > 0
    assert isinstance(result.gravy, float)
    assert result.protein_id == "protein_1"