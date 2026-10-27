from pathlib import Path

import pytest

from app.services.analysis_service import _resolve_host_reference


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

    database, should_run = _resolve_host_reference("mouse")

    assert database is not None
    assert Path(f"{database}.pin").is_file()
    assert should_run is True


@pytest.mark.parametrize("reference", ["human", "pig"])
def test_unconfigured_host_reference_does_not_use_legacy_database(
    monkeypatch,
    reference,
):
    monkeypatch.setenv("HOST_BLAST_DATABASE", "/refs/legacy")
    monkeypatch.delenv(
        f"HOST_BLAST_DATABASE_{reference.upper()}",
        raising=False,
    )

    database, should_run = _resolve_host_reference(reference)

    assert database is None
    assert should_run is True


def test_invalid_host_reference_raises_value_error():
    with pytest.raises(ValueError, match="host_reference"):
        _resolve_host_reference("dog")