import sqlite3

import pytest

from app.integrations.epath_essentiality import (
    fetch_epath_essentiality_evidence,
)


@pytest.fixture
def epath_db(tmp_path):
    """Create a small ePath-shaped database for isolated tests."""
    path = tmp_path / "epath.sqlite3"

    with sqlite3.connect(path) as connection:
        connection.executescript("""
            CREATE TABLE epath_experimental_records (
                organism_abbreviation TEXT,
                organism TEXT,
                essential_gene_count INTEGER,
                screen_condition TEXT,
                reference TEXT
            );

            CREATE TABLE epath_gene (
                id INTEGER PRIMARY KEY,
                organism TEXT,
                organism_abbreviation TEXT,
                gene_id TEXT,
                ko_id TEXT,
                annotation TEXT,
                score1 TEXT,
                score2 TEXT
            );

            CREATE TABLE epath_ko_essentiality (
                ko_id TEXT,
                organism_abbreviation TEXT,
                symbol TEXT,
                PRIMARY KEY (ko_id, organism_abbreviation)
            );

            INSERT INTO epath_experimental_records
            VALUES (
                'eco',
                'Escherichia coli K-12 MG1655',
                300,
                'laboratory',
                'Example reference'
            );

            INSERT INTO epath_gene
            VALUES (
                1,
                'Escherichia coli K-12 MG1655',
                'eco',
                'b3945',
                'K00005',
                'Example annotation',
                NULL,
                NULL
            );

            INSERT INTO epath_ko_essentiality
            VALUES ('K00005', 'eco', 'x');

            INSERT INTO epath_ko_essentiality
            VALUES ('K00006', 'eco', '*');

            INSERT INTO epath_ko_essentiality
            VALUES ('K00007', 'eco', 'o');

            INSERT INTO epath_ko_essentiality
            VALUES ('K00008', 'eco', '-');
        """)

    return str(path)


def test_gene_lookup_returns_organism_specific_evidence(epath_db):
    result = fetch_epath_essentiality_evidence(
        organism="eco",
        gene_id="b3945",
        database_path=epath_db,
    )

    assert result["status"] == "available"
    assert len(result["evidence"]) == 1

    evidence = result["evidence"][0]
    assert evidence.gene_id == "b3945"
    assert evidence.organism == "Escherichia coli K-12 MG1655"
    assert evidence.essentiality_status == "non-essential"
    assert evidence.source == "ePath"


def test_essential_symbol_is_classified_as_essential(epath_db):
    result = fetch_epath_essentiality_evidence(
        organism="eco",
        ko_id="K00006",
        database_path=epath_db,
    )

    assert result["status"] == "available"
    assert result["evidence"][0].essentiality_status == "essential"
    assert result["evidence"][0].gene_id == "KO:K00006"


@pytest.mark.parametrize("symbol", ["o", "-"])
def test_unclassified_symbols_do_not_create_definitive_evidence(
    epath_db, symbol
):
    ko_id = "K00007" if symbol == "o" else "K00008"

    result = fetch_epath_essentiality_evidence(
        organism="eco",
        ko_id=ko_id,
        database_path=epath_db,
    )

    assert result["status"] == "unclassified"
    assert result["evidence"] == []


def test_requires_organism(epath_db):
    result = fetch_epath_essentiality_evidence(
        organism=None,
        gene_id="b3945",
        database_path=epath_db,
    )

    assert result["status"] == "organism_required"
    assert result["evidence"] == []


def test_requires_verified_gene_or_ko_identifier(epath_db):
    result = fetch_epath_essentiality_evidence(
        organism="eco",
        database_path=epath_db,
    )

    assert result["status"] == "identifier_required"
    assert result["evidence"] == []


def test_rejects_gene_identifier_from_another_organism(epath_db):
    result = fetch_epath_essentiality_evidence(
        organism="eco",
        gene_id="not-a-real-gene",
        database_path=epath_db,
    )

    assert result["status"] == "no_matching_evidence"
    assert result["evidence"] == []


def test_does_not_transfer_ko_evidence_between_organisms(epath_db):
    result = fetch_epath_essentiality_evidence(
        organism="Different bacterium",
        ko_id="K00005",
        database_path=epath_db,
    )

    assert result["status"] == "organism_not_found"
    assert result["evidence"] == []


def test_rejects_conflicting_gene_and_ko_identifiers(epath_db):
    result = fetch_epath_essentiality_evidence(
        organism="eco",
        gene_id="b3945",
        ko_id="K00006",
        database_path=epath_db,
    )

    assert result["status"] == "identifier_conflict"
    assert result["evidence"] == []


def test_reports_missing_database(tmp_path):
    result = fetch_epath_essentiality_evidence(
        organism="eco",
        ko_id="K00005",
        database_path=str(tmp_path / "missing.sqlite3"),
    )

    assert result["status"] == "not_configured"
    assert result["evidence"] == []
