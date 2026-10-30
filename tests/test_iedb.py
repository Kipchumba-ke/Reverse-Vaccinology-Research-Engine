import pytest
import requests

from app.integrations import iedb

# Hand-written samples in the layout the parsers expect. They are not
# captured IEDB responses.
MHCI = (
    "allele\tseq_num\tstart\tend\tlength\tpeptide\tscore\tpercentile_rank\n"
    "HLA-A*02:01\t1\t3\t11\t9\tLLLALLLAL\t0.91\t0.20\n"
    "HLA-A*02:01\t1\t4\t12\t9\tLLALLLALV\t0.30\t4.50\n"
    "HLA-A*01:01\t1\t3\t11\t9\tLLLALLLAL\t0.80\t0.60\n"
)
MHCII = (
    "allele\tseq_num\tstart\tend\tlength\tcore_peptide\tpeptide\tscore\t"
    "rank\n"
    "HLA-DRB1*01:01\t1\t5\t19\t15\tLALLLALVL\tLLLALLLALVLAAVS\t0.9\t2.5\n"
    "HLA-DRB1*01:01\t1\t6\t20\t15\tALLLALVLA\tLLALLLALVLAAVSA\t0.1\t40.0\n"
)
BCELL = (
    "Position\tResidue\tScore\tAssignment\n"
    + "".join(
        f"{i}\tA\t{0.9 if 5 <= i <= 12 else 0.1}\t"
        f"{'E' if 5 <= i <= 12 else '-'}\n"
        for i in range(1, 21)
    )
)


def test_mhci_table_is_parsed_by_column_name():
    rows = iedb.parse_binding_table(MHCI)

    assert len(rows) == 3
    assert rows[0]["allele"] == "HLA-A*02:01"
    assert rows[0]["peptide"] == "LLLALLLAL"
    assert rows[0]["percentile_rank"] == 0.20
    assert rows[0]["start"] == 3 and rows[0]["end"] == 11


def test_mhcii_table_uses_rank_and_core_columns():
    rows = iedb.parse_binding_table(MHCII)

    assert rows[0]["percentile_rank"] == 2.5
    assert rows[0]["core"] == "LALLLALVL"
    assert rows[0]["peptide"] == "LLLALLLALVLAAVS"


def test_reordered_columns_are_fine():
    text = "percentile_rank\tpeptide\tstart\tallele\n1.0\tAAAAAAAAA\t2\tX\n"

    row = iedb.parse_binding_table(text)[0]

    assert row["end"] == 10 and row["allele"] == "X"


@pytest.mark.parametrize("text", [
    "",
    "something else\n1\t2\n",
    "allele\tpeptide\tstart\nX\tAAAAAAAAA\t1\n",
])
def test_unexpected_tables_are_rejected_with_a_reason(text):
    with pytest.raises(ValueError):
        iedb.parse_binding_table(text)


def test_malformed_rows_are_skipped():
    text = (
        "allele\tstart\tpeptide\tpercentile_rank\n"
        "X\t1\tAAAAAAAAA\tnot-a-number\n"
        "X\t2\tAAAAAAAAA\t0.5\n"
    )

    assert len(iedb.parse_binding_table(text)) == 1


def test_binders_group_by_peptide_across_alleles_and_sort():
    binders = iedb.collect_binders(iedb.parse_binding_table(MHCI), 1.0)

    assert len(binders) == 1
    assert binders[0]["allele_count"] == 2
    assert binders[0]["best_percentile_rank"] == 0.20
    assert [a["allele"] for a in binders[0]["alleles"]] == [
        "HLA-A*02:01", "HLA-A*01:01",
    ]


def test_cutoff_excludes_weak_predictions():
    assert iedb.collect_binders(iedb.parse_binding_table(MHCI), 0.1) == []


def test_bcell_regions_use_the_assignment_column():
    regions = iedb.bcell_regions(iedb.parse_bcell_table(BCELL))

    assert regions == [
        {"start": 5, "end": 12, "length": 8, "mean_score": 0.9},
    ]


def test_bcell_regions_fall_back_to_the_score_cutoff():
    text = "Position\tResidue\tScore\n" + "".join(
        f"{i}\tA\t{0.7 if 2 <= i <= 8 else 0.2}\n" for i in range(1, 12)
    )

    regions = iedb.bcell_regions(iedb.parse_bcell_table(text))

    assert [(r["start"], r["end"]) for r in regions] == [(2, 8)]


def test_short_bcell_runs_are_dropped():
    text = "Position\tResidue\tScore\tAssignment\n" + "".join(
        f"{i}\tA\t0.9\t{'E' if i in (3, 4) else '-'}\n" for i in range(1, 9)
    )

    assert iedb.bcell_regions(iedb.parse_bcell_table(text)) == []


def test_bcell_header_is_required():
    with pytest.raises(ValueError):
        iedb.parse_bcell_table("nothing useful\n")


class FakeResponse:
    def __init__(self, text, status=200):
        self.text = text
        self.status = status

    def raise_for_status(self):
        if self.status >= 400:
            raise requests.HTTPError(f"{self.status} error")


@pytest.fixture
def fake_iedb(monkeypatch):
    calls = []

    def post(url, data, timeout):
        calls.append((url, data))
        if url.endswith("/mhci/"):
            return FakeResponse(MHCI)
        if url.endswith("/mhcii/"):
            return FakeResponse(MHCII)
        return FakeResponse(BCELL)

    monkeypatch.setattr(iedb.requests, "post", post)
    monkeypatch.setenv("IEDB_MHCI_ALLELES", "HLA-A*02:01")
    monkeypatch.setenv("IEDB_MHCII_ALLELES", "HLA-DRB1*01:01")
    return calls


def test_full_prediction_combines_the_three_services(fake_iedb):
    result = iedb.fetch_epitope_predictions("A" * 30)

    assert result["status"] == "completed"
    assert result["mhc_class_i"]["binders"]
    assert result["mhc_class_ii"]["binders"]
    assert result["b_cell"]["regions"][0]["start"] == 5
    assert result["overlaps"]
    assert result["overlaps"][0]["mhc_i_binders"] >= 1


def test_requests_use_documented_parameters(fake_iedb):
    iedb.fetch_epitope_predictions("A" * 30)

    by_tool = {url.rsplit("/", 2)[-2]: data for url, data in fake_iedb}

    assert by_tool["mhci"] == {
        "method": "recommended", "sequence_text": "A" * 30,
        "allele": "HLA-A*02:01", "length": "9",
    }
    assert by_tool["mhcii"]["length"] == "15"
    assert by_tool["bcell"] == {
        "method": "Bepipred-2.0", "sequence_text": "A" * 30,
    }


def test_one_request_per_allele(monkeypatch, fake_iedb):
    monkeypatch.setenv("IEDB_MHCI_ALLELES", "HLA-A*02:01,HLA-A*01:01")

    iedb.fetch_epitope_predictions("A" * 30)

    mhci_calls = [c for c in fake_iedb if c[0].endswith("/mhci/")]
    assert len(mhci_calls) == 2


def test_a_failing_allele_is_recorded_not_fatal(monkeypatch, fake_iedb):
    def post(url, data, timeout):
        if data.get("allele") == "HLA-A*01:01":
            raise requests.ConnectionError("down")
        return FakeResponse(MHCI if "/mhci/" in url else
                            MHCII if "/mhcii/" in url else BCELL)

    monkeypatch.setattr(iedb.requests, "post", post)
    monkeypatch.setenv("IEDB_MHCI_ALLELES", "HLA-A*01:01,HLA-A*02:01")

    result = iedb.fetch_epitope_predictions("A" * 30)

    assert result["status"] == "completed"
    assert "HLA-A*01:01" in result["mhc_class_i"]["alleles_failed"]


def test_total_failure_is_reported(monkeypatch):
    def post(url, data, timeout):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(iedb.requests, "post", post)
    monkeypatch.setenv("IEDB_MHCI_ALLELES", "HLA-A*02:01")
    monkeypatch.setenv("IEDB_MHCII_ALLELES", "HLA-DRB1*01:01")

    result = iedb.fetch_epitope_predictions("A" * 30)

    assert result["status"] == "lookup_failed"
    assert "IEDB request failed" in result["message"]


def test_long_sequences_are_not_sent(monkeypatch):
    monkeypatch.setenv("IEDB_MAX_SEQUENCE_LENGTH", "10")

    result = iedb.fetch_epitope_predictions("A" * 30)

    assert result["status"] == "not_performed"


def test_bad_configuration_is_reported(monkeypatch):
    monkeypatch.setenv("IEDB_MHCI_RANK_CUTOFF", "abc")

    result = iedb.fetch_epitope_predictions("A" * 30)

    assert result["status"] == "lookup_failed"
    assert "IEDB_MHCI_RANK_CUTOFF" in result["message"]


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv("IEDB_ENABLED", raising=False)

    assert iedb.is_iedb_enabled() is False


def test_peptide_windows_gain_epitope_fields(fake_iedb):
    prediction = iedb.fetch_epitope_predictions("A" * 30)
    windows = [
        {"start": 1, "end": 15, "sequence": "A" * 15},
        {"start": 20, "end": 30, "sequence": "A" * 11},
    ]

    annotated = iedb.annotate_peptides_with_epitopes(windows, prediction)

    assert annotated[0]["overlaps_b_cell_epitope"] is True
    assert annotated[0]["mhc_i_binder_alleles"] == 2
    assert annotated[1]["overlaps_b_cell_epitope"] is False
    assert annotated[1]["mhc_i_binder_alleles"] == 0


def test_annotation_is_a_no_op_after_failure():
    windows = [{"start": 1, "end": 15, "sequence": "A" * 15}]

    assert iedb.annotate_peptides_with_epitopes(
        windows, {"status": "lookup_failed"}
    ) == windows


def test_repeated_rows_for_one_allele_are_counted_once():
    text = (
        "allele\tstart\tend\tpeptide\tpercentile_rank\n"
        "HLA-A*02:01\t3\t11\tLLLALLLAL\t0.9\n"
        "HLA-A*02:01\t3\t11\tLLLALLLAL\t0.3\n"
    )

    binders = iedb.collect_binders(iedb.parse_binding_table(text), 1.0)

    assert binders[0]["allele_count"] == 1
    assert binders[0]["alleles"][0]["percentile_rank"] == 0.3
