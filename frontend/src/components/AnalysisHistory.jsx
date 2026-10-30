import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { deleteAnalysis ,getAnalysisHistory } from '../services/historyService'

function formatDate(value) {
  if (!value) return 'Date unavailable'

  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? 'Date unavailable'
    : date.toLocaleString()
}

function AnalysisHistory() {
  const [analyses, setAnalyses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [deletingId, setDeletingId] = useState(null)
  const [deleteError, setDeleteError] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadHistory() {
      try {
        const token = localStorage.getItem('token')

        if (!token) {
          throw new Error('Please log in to view your analysis history.')
        }

        const result = await getAnalysisHistory(token)

        if (!cancelled) {
          setAnalyses(result)
          setError('')
        }
      } catch (err) {
        if (!cancelled) setError(err.message || 'Unable to load history.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    loadHistory()

    return () => {
      cancelled = true
    }
  }, [])

  async function handleDelete(analysis) {
    const proteinName = analysis.protein_name || 'this analysis'

    const confirmed = window.confirm(
      `Are you sure you want to delete "${proteinName}"? This action cannot be undone.`,
    )

    if (!confirmed) return

    const token = localStorage.getItem('token')

    if (!token) {
      setDeleteError('Please log in to delete an analysis.')
      return
    }

    setDeletingId(analysis.analysis_id)
    setDeleteError('')
    setSuccessMessage('')

    try {
      await deleteAnalysis(analysis.analysis_id, token)

      setAnalyses((current) =>
        current.filter(
          (item) => item.analysis_id !== analysis.analysis_id,
        ),
      )

      setSuccessMessage(`${proteinName} was deleted successfully.`)
    } catch (err) {
      setDeleteError(err.message || 'Unable to delete analysis.')
    } finally {
      setDeletingId(null)
    }
  }

  if (loading) {
    return <main id="main" className="analysis-page"><p>Loading analysis history...</p></main>
  }

  return (
    <main id="main" className="analysis-page">
      <header className="workspace-header">
        <p className="kicker">Saved reports</p>
        <h1>Analysis History</h1>
        <p>Review your previously submitted protein analyses.</p>
      </header>

      {error && <p role="alert" className="history-error">{error}</p>}
      {deleteError && <p role="alert" className="history-error">{deleteError}</p>}
      {successMessage && <p role="alert" className="history-success">{successMessage}</p>}

      {!error && analyses.length === 0 && (
        <p>You have no saved analyses yet.</p>
      )}

      {analyses.length > 0 && (
        <div className="history-list">
          {analyses.map((analysis) => (
            <article className="history-item" key={analysis.analysis_id}>
              <div>
                <h2>{analysis.protein_name || 'Unnamed protein'}</h2>
                <p>{analysis.organism || 'Organism not specified'}</p>
                {analysis.accession && <p>Accession: {analysis.accession}</p>}
                <p>Created: {formatDate(analysis.created_at)}</p>
                <p>
                  Status: <strong>{analysis.status}</strong>
                </p>
              </div>

              <div className='view-delete'>
                <Link to={`/analyses/${analysis.analysis_id}`}>
                  View analysis
                </Link>

                <button
                  type="button"
                  className="delete-button"
                  onClick={() => handleDelete(analysis)}
                  disabled={deletingId === analysis.analysis_id}
                  aria-label={`Delete ${analysis.protein_name || 'analysis'}`}
                >
                  {deletingId === analysis.analysis_id
                    ? 'Deleting...'
                    : 'Delete'}
                </button>
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  )
}

export default AnalysisHistory
