
from unittest.mock import Mock, patch

import pytest
import requests

from app.integrations.ncbi import fetch_protein_record
from app.services.analysis_service import fetch_localization_result


NCBI_RECORD = """LOCUS       ALR82097                100 aa            linear   VRL
DEFINITION  polymerase [Zaire ebolavirus].
ACCESSION   ALR82097
VERSION     ALR82097.1
FEATURES             Location/Qualifiers
     Protein         1..100
                     /product="polymerase"
                     /subcellular_location="Virion"
ORIGIN
        1 mkkllaaacc gggttt
//
"""


def mock_response(text):
    response = Mock()
    response.text = text
    response.raise_for_status.return_value = None
    return response


@patch("app.integrations.ncbi.requests.get")
def test_fetches_ncbi_record_and_preserves_version(mock_get):
    mock_get.return_value = mock_response(NCBI_RECORD)

    result = fetch_protein_record("ALR82097.1")

    assert result["accession"] == "ALR82097.1"
    assert result["source"] == "NCBI Protein"
    assert result["localization_status"] == "available"
    assert result["localization_annotations"] == [
        {"location": "Virion", "evidence_codes": []}
    ]

    _, kwargs = mock_get.call_args
    assert kwargs["params"]["db"] == "protein"
    assert kwargs["params"]["id"] == "ALR82097.1"


@patch("app.integrations.ncbi.requests.get")
def test_successful_record_without_localization_is_not_a_failure(
    mock_get,
):
    record_without_location = NCBI_RECORD.replace(
        '                     /subcellular_location="Virion"\n',
        "",
    )
    mock_get.return_value = mock_response(record_without_location)

    result = fetch_protein_record("ALR82097.1")

    assert result["accession"] == "ALR82097.1"
    assert result["localization_annotations"] == []
    assert result["localization_status"] == "no_annotations"


@patch("app.integrations.ncbi.requests.get")
def test_rejects_invalid_ncbi_response(mock_get):
    mock_get.return_value = mock_response(
        "Invalid accession"
    )

    with pytest.raises(RuntimeError, match="valid protein record"):
        fetch_protein_record("ALR82097.1")


@patch("app.integrations.ncbi.requests.get")
def test_handles_network_errors(mock_get):
    mock_get.side_effect = requests.Timeout("request timed out")

    with pytest.raises(RuntimeError, match="lookup failed"):
        fetch_protein_record("ALR82097.1")


def test_rejects_empty_accession():
    with pytest.raises(ValueError, match="accession is required"):
        fetch_protein_record("")


@patch("app.services.analysis_service.convert_uniprot_localizations")
@patch("app.services.analysis_service.fetch_protein_record")
def test_service_routes_versioned_accession_to_ncbi(
    mock_fetch, mock_convert
):
    mock_fetch.return_value = {
        "source": "NCBI Protein",
        "localization_annotations": [{"location": "Virion"}],
    }
    mock_convert.return_value = ["localization-evidence"]

    result = fetch_localization_result("ALR82097.1")

    mock_fetch.assert_called_once_with("ALR82097.1")
    assert result["status"] == "available"
    assert result["source"] == "NCBI Protein"
    assert result["evidence"] == ["localization-evidence"]


@patch("app.services.analysis_service.fetch_protein_annotation")
def test_service_reports_no_localization_annotations(mock_fetch):
    mock_fetch.return_value = {
        "localization_annotations": [],
    }

    with patch(
        "app.services.analysis_service.convert_uniprot_localizations",
        return_value=[],
    ):
        result = fetch_localization_result("P0DTC2")

    assert result["status"] == "no_annotations"
    assert result["source"] == "UniProt"
    assert result["evidence"] == []


def test_service_reports_missing_accession_without_lookup():
    result = fetch_localization_result(None)

    assert result["status"] == "not_attempted"
    assert result["evidence"] == []
