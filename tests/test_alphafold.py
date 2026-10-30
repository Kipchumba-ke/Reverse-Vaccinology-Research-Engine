import pytest
import requests

from app.integrations import alphafold


def atom(serial, name, residue, position, plddt):
    return (
        f"ATOM  {serial:5d} {name:^4s} {residue:3s} A{position:4d}    "
        f"{1.0:8.3f}{2.0:8.3f}{3.0:8.3f}{1.0:6.2f}{plddt:6.2f}           C"
    )


PDB = "\n".join([
    atom(1, "N", "MET", 1, 95.0),
    atom(2, "CA", "MET", 1, 95.0),
    atom(3, "N", "LYS", 2, 72.5),
    atom(4, "CA", "LYS", 2, 72.5),
    atom(5, "CA", "THR", 3, 41.2),
    "TER",
])

ENTRY = [{
    "entryId": "AF-P0A911-F1",
    "latestVersion": 4,
    "modelCreatedDate": "2022-06-01",
    "organismScientificName": "Escherichia coli",
    "uniprotSequence": "MKT",
    "uniprotStart": 1,
    "uniprotEnd": 3,
    "pdbUrl": "https://alphafold.ebi.ac.uk/files/AF-P0A911-F1-model_v4.pdb",
    "paeImageUrl": "https://alphafold.ebi.ac.uk/files/pae.png",
}]


class Response:
    def __init__(self, status=200, payload=None, text=""):
        self.status_code = status
        self._payload = payload
        self.text = text
        self.content = text.encode()

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


@pytest.fixture(autouse=True)
def clear_cache():
    alphafold.fetch_structure.cache_clear()


def test_pdb_helper_reads_one_plddt_per_residue():
    assert alphafold.plddt_from_pdb(PDB) == [
        {"position": 1, "plddt": 95.0},
        {"position": 2, "plddt": 72.5},
        {"position": 3, "plddt": 41.2},
    ]


@pytest.mark.parametrize("value,band", [
    (95, "very_high"), (90, "high"), (71, "high"),
    (70, "low"), (51, "low"), (50, "very_low"),
])
def test_confidence_bands_follow_alphafold_thresholds(value, band):
    assert alphafold.confidence_band(value) == band


@pytest.mark.parametrize("accession", ["P0A911", "p0a911", "A0A024R161"])
def test_valid_accessions_are_accepted(accession):
    assert alphafold.normalise_accession(accession) == accession.upper()


@pytest.mark.parametrize("accession", [
    "", "WP_000001.1", "../etc/passwd", "P0A91", "P0A911/../x",
])
def test_other_identifiers_are_rejected(accession):
    with pytest.raises(ValueError):
        alphafold.normalise_accession(accession)


def test_structure_is_fetched_and_summarised(monkeypatch):
    def get(url, timeout):
        if url.endswith("/P0A911"):
            return Response(payload=ENTRY)
        return Response(text=PDB)

    monkeypatch.setattr(alphafold.requests, "get", get)

    result = alphafold.fetch_structure("p0a911")

    assert result["accession"] == "P0A911"
    assert result["entry_id"] == "AF-P0A911-F1"
    assert result["reference_sequence"] == "MKT"
    assert result["mean_plddt"] == 69.6
    assert result["pdb"].startswith("ATOM")
    assert len(result["confidence"]) == 3


def test_missing_model_raises_not_found(monkeypatch):
    monkeypatch.setattr(
        alphafold.requests, "get", lambda url, timeout: Response(status=404)
    )

    with pytest.raises(alphafold.StructureNotFound):
        alphafold.fetch_structure("P0A911")


def test_unexpected_download_host_is_refused(monkeypatch):
    bad = [{**ENTRY[0], "pdbUrl": "https://evil.example.com/x.pdb"}]
    monkeypatch.setattr(
        alphafold.requests, "get", lambda url, timeout: Response(payload=bad)
    )

    with pytest.raises(RuntimeError, match="unexpected file location"):
        alphafold.fetch_structure("P0A911")


def test_http_downgrade_is_refused(monkeypatch):
    bad = [{**ENTRY[0], "pdbUrl": "http://alphafold.ebi.ac.uk/x.pdb"}]
    monkeypatch.setattr(
        alphafold.requests, "get", lambda url, timeout: Response(payload=bad)
    )

    with pytest.raises(RuntimeError):
        alphafold.fetch_structure("P0A911")


def test_network_errors_become_runtime_errors(monkeypatch):
    def get(url, timeout):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(alphafold.requests, "get", get)

    with pytest.raises(RuntimeError, match="AlphaFold request failed"):
        alphafold.fetch_structure("P0A911")


def test_oversized_models_are_refused(monkeypatch):
    monkeypatch.setattr(alphafold, "MAX_PDB_BYTES", 10)
    monkeypatch.setattr(
        alphafold.requests, "get",
        lambda url, timeout: Response(payload=ENTRY) if url.endswith("11")
        else Response(text=PDB),
    )

    with pytest.raises(RuntimeError, match="too large"):
        alphafold.fetch_structure("P0A911")
