from app.models.analysis import Analysis
from app.models.analysis_orm import AnalysisModel


class AnalysisRepository:
    def __init__(self, session):
        self.session = session

    @staticmethod
    def _to_orm(analysis: Analysis) -> AnalysisModel:
        return AnalysisModel(
            id=analysis.id,
            protein_id=analysis.protein_id,
            protein_name=analysis.protein_name,
            organism=analysis.organism,
            accession=analysis.accession,
            sequence=analysis.sequence,
            status=analysis.status,
        )

    @staticmethod
    def _to_domain(model: AnalysisModel) -> Analysis:
        return Analysis(
            id=model.id,
            protein_id=model.protein_id,
            protein_name=model.protein_name,
            organism=model.organism,
            accession=model.accession,
            sequence=model.sequence,
            status=model.status,
        )

    def save(self, analysis: Analysis) -> Analysis:
        model = self._to_orm(analysis)

        self.session.add(model)
        self.session.flush()

        return analysis

    def find_by_id(self, analysis_id):
        model = self.session.get(AnalysisModel, analysis_id)

        if model is None:
            return None

        return self._to_domain(model)