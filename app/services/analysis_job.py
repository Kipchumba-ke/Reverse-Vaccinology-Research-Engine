from app.services.analysis_execution import execute_analysis


class AnalysisJob:
    def __init__(self, analysis, repository=None):
        self.analysis = analysis
        self.repository = repository

    def run(self):
        return execute_analysis(
            self.analysis,
            self.repository,
        )