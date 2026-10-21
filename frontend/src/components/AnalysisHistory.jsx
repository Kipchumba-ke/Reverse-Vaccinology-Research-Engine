import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getAnalysisHistory } from '../services/historyService'

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

  if (loading) {
    return <main className="analysis-page"><p>Loading analysis history...</p></main>
  }

  return (
    <main className="analysis-page">
      <h1>Analysis History</h1>
      <p>Review your previously submitted protein analyses.</p>

      {error && <p role="alert">{error}</p>}

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

              <Link to={`/analyses/${analysis.analysis_id}`}>
                View analysis
              </Link>
            </article>
          ))}
        </div>
      )}
    </main>
  )
}

export default AnalysisHistory
