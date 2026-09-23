from app.models.analysis import Analysis


class AnalysisRepository:
    def __init__(self):
        self._analyses = {}

    def save(self, analysis: Analysis) -> Analysis:
        self._analyses[analysis.id] = analysis
        return analysis

    def find_by_id(self, analysis_id: int):
        return self._analyses.get(analysis_id)