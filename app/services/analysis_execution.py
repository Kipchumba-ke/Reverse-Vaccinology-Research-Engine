from app.services.analysis_service import analyze_sequence


def execute_analysis(analysis, repository=None):
    analysis.status = "running"

    if repository is not None:
        repository.update(analysis)

    try:
        result = analyze_sequence(
            analysis.sequence,
            protein_id=analysis.protein_id,
            protein_name=analysis.protein_name,
            organism=analysis.organism,
            accession=analysis.accession,
        )
    except Exception:
        analysis.status = "failed"

        if repository is not None:
            repository.update(analysis)
        
        raise

    analysis.status = "completed"
    
    if repository is not None:
        repository.update(analysis)

    return result