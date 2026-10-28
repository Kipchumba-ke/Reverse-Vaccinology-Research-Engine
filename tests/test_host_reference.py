from pathlib import Path

import pytest

from app.services.analysis_service import _resolve_host_reference


def mock_local_database_availability(monkeypatch, available_databases):
    original_is_file = Path.is_file

    def mocked_is_file(path):
        path_string = str(path)

        if path_string.endswith(".pin"):
            return path_string in available_databases

        return original_is_file(path)

    monkeypatch.setattr(Path, "is_file", mocked_is_file)


def test_unselected_host_reference_uses_legacy_database(monkeypatch):
    monkeypatch.setenv("HOST_BLAST_DATABASE", "/refs/legacy")

    database, should_run = _resolve_host_reference(None)

    assert database == "/refs/legacy"
    assert should_run is True


def test_none_disables_host_search(monkeypatch):
    monkeypatch.setenv("HOST_BLAST_DATABASE", "/refs/legacy")

    database, should_run = _resolve_host_reference("none")

    assert database is None
    assert should_run is False


def test_mouse_uses_configured_database(monkeypatch):
    monkeypatch.setenv(
        "HOST_BLAST_DATABASE_MOUSE",
        "/refs/mouse/custom_db",
    )

    database, should_run = _resolve_host_reference("mouse")

    assert database == "/refs/mouse/custom_db"
    assert should_run is True


def test_mouse_uses_existing_local_database(monkeypatch):
    monkeypatch.delenv("HOST_BLAST_DATABASE_MOUSE", raising=False)

    project_root = Path(__file__).resolve().parents[1]
    local_database = (
        project_root / "data" / "reference" / "mouse" / "mouse_proteome_db"
    ).resolve()

    mock_local_database_availability(
        monkeypatch,
        {f"{local_database}.pin"},
    )

    database, should_run = _resolve_host_reference("mouse")

    assert database == str(local_database)
    assert should_run is True


@pytest.mark.parametrize(
    ("reference", "environment_variable", "expected_suffix"),
    [
        (
            "human",
            "HOST_BLAST_DATABASE_HUMAN",
            "data/reference/human/human_proteome_db",
        ),
        (
            "pig",
            "HOST_BLAST_DATABASE_PIG",
            "data/reference/pig/pig_proteome_db",
        ),
    ],
)
def test_host_reference_uses_existing_local_database(
    monkeypatch,
    reference,
    environment_variable,
    expected_suffix,
):
    monkeypatch.delenv(environment_variable, raising=False)
    monkeypatch.setenv("HOST_BLAST_DATABASE", "/refs/legacy")

    project_root = Path(__file__).resolve().parents[1]
    local_database = (project_root / expected_suffix).resolve()

    mock_local_database_availability(
        monkeypatch,
        {f"{local_database}.pin"},
    )

    database, should_run = _resolve_host_reference(reference)

    assert database is not None
    assert database.endswith(expected_suffix)
    assert Path(f"{database}.pin").is_file()
    assert database != "/refs/legacy"
    assert should_run is True


@pytest.mark.parametrize(
    ("reference", "environment_variable"),
    [
        ("human", "HOST_BLAST_DATABASE_HUMAN"),
        ("mouse", "HOST_BLAST_DATABASE_MOUSE"),
        ("pig", "HOST_BLAST_DATABASE_PIG"),
    ],
)
def test_configured_host_database_overrides_local_database(
    monkeypatch,
    reference,
    environment_variable,
):
    monkeypatch.setenv(environment_variable, "/refs/custom_db")

    database, should_run = _resolve_host_reference(reference)

    assert database == "/refs/custom_db"
    assert should_run is True


def test_invalid_host_reference_raises_value_error():
    with pytest.raises(ValueError, match="host_reference"):
        _resolve_host_reference("dog")


@pytest.mark.parametrize("reference", ["human", "mouse", "pig"])
def test_host_reference_without_local_database_returns_none(
    monkeypatch,
    reference,
):
    monkeypatch.delenv(
        f"HOST_BLAST_DATABASE_{reference.upper()}",
        raising=False,
    )
    monkeypatch.delenv("HOST_BLAST_DATABASE", raising=False)

    mock_local_database_availability(monkeypatch, set())

    database, should_run = _resolve_host_reference(reference)

    assert database is None
    assert should_run is True
