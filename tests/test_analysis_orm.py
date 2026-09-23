from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID

from app.database import Base
from app.models.analysis_orm import AnalysisModel


def test_analysis_model_maps_to_analyses_table():
    inspector = inspect(AnalysisModel)

    assert inspector.persist_selectable.name == "analyses"

def test_analysis_model_has_expected_columns():
    columns = {
        column.name
        for column in AnalysisModel.__table__.columns
    }

    assert columns == {
        "id",
        "protein_id",
        "protein_name",
        "organism",
        "accession",
        "sequence",
        "status",
    }

def test_analysis_model_requires_sequence_and_status():
    sequence_column = AnalysisModel.__table__.c.sequence
    status_column = AnalysisModel.__table__.c.status

    assert sequence_column.nullable is False
    assert status_column.nullable is False

def test_analysis_model_id_is_primary_key():
    primary_keys = {
        column.name
        for column in AnalysisModel.__table__.primary_key.columns
    }

    assert primary_keys == {"id"}

def test_analysis_model_id_uses_postgresql_uuid():
    id_column = AnalysisModel.__table__.c.id

    assert isinstance(id_column.type, PostgreSQLUUID)
    assert id_column.type.as_uuid is True