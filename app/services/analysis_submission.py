from app.models.analysis import Analysis


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
        epath_gene_id=None,
        epath_ko_id=None,
    ):
        analysis = Analysis(
            user_id=user_id,
            protein_id=protein_id,
            protein_name=protein_name,
            organism=organism,
            accession=accession,
            sequence=sequence,
            epath_gene_id=epath_gene_id,
            epath_ko_id=epath_ko_id,
        )

        self.repository.save(analysis)

        return analysis.id