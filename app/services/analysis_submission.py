from app.models.analysis import Analysis
from app.services.analysis_job import AnalysisJob


class AnalysisSubmissionService:
    def __init__(self, repository, queue):
        self.repository = repository
        self.queue = queue

    def submit(
        self,
        sequence,
        protein_id=None,
        protein_name=None,
        organism=None,
        accession=None,
        user_id=None,
    ):
        analysis = Analysis(
            user_id=user_id,
            protein_id=protein_id,
            protein_name=protein_name,
            organism=organism,
            accession=accession,
            sequence=sequence,
        )

        self.repository.save(analysis)

        job = AnalysisJob(
            analysis,
            self.repository,
        )
        self.queue.enqueue(job)

        return analysis.id