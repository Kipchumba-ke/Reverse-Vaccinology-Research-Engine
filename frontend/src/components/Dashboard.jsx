import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getAnalysisHistory } from '../services/historyService'
import ThemeToggle from './ThemeToggle'
import './Shell.css'
import './Dashboard.css'

const ACTIVE_ANALYSIS_KEY = 'activeAnalysisId'

function formatDate(value) {
  if (!value) return 'Date unavailable'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return 'Date unavailable'

  return new Intl.DateTimeFormat(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(date)
}

function formatStatus(status) {
  if (!status) return 'Unknown'

  return String(status).replace(/[_-]+/g, ' ')
}

function statusMark(status) {
  switch (String(status || '').toLowerCase()) {
    case 'completed':
      return '✓'
    case 'failed':
      return '✕'
    default:
      return '…'
  }
}

function Dashboard({ onLogout }) {
  const navigate = useNavigate()
  const [analyses, setAnalyses] = useState([])
  const [loading, setLoading] = useState(true)
  const [historyError, setHistoryError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadRecentAnalyses() {
      try {
        const token = localStorage.getItem('token')

        if (!token) {
          navigate('/login', { replace: true })
          return
        }

        const results = await getAnalysisHistory(token)

        if (!cancelled) {
          setAnalyses(Array.isArray(results) ? results.slice(0, 8) : [])
        }
      } catch (error) {
        if (!cancelled) {
          setHistoryError(error.message || 'Unable to load recent analyses.')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadRecentAnalyses()

    return () => {
      cancelled = true
    }
  }, [navigate])

  function handleLogout() {
    localStorage.removeItem('token')
    localStorage.removeItem(ACTIVE_ANALYSIS_KEY)
    onLogout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="shell">
      <a className="skip-link" href="#main">Skip to main content</a>

      <header className="site-header">
        <div className="site-header-inner">
          <Link className="wordmark" to="/dashboard" aria-label="ReverseVax dashboard">
            ReverseVax
            <span>evidence ledger</span>
          </Link>

          <nav className="site-nav" aria-label="Main navigation">
            <Link to="/dashboard" aria-current="page">Dashboard</Link>
            <Link to="/analyses">New analysis</Link>
            <Link to="/history">Analysis history</Link>
          </nav>

          <div className="site-actions">
            <ThemeToggle />
            <button type="button" className="btn btn-quiet" onClick={handleLogout}>
              Log out
            </button>
          </div>
        </div>
      </header>

      <main id="main" className="dashboard-page">
        <section className="dash-intro" aria-labelledby="dash-title">
          <p className="kicker">Workbench</p>
          <h1 id="dash-title">From protein sequences to evidence you can audit.</h1>
          <p className="lede">
            Submit a sequence, wait for the pipeline, then read each result
            beside its source and its limits. Findings are computational
            screens that need laboratory follow-up.
          </p>
          <div className="dash-actions">
            <Link className="btn btn-primary" to="/analyses">New analysis</Link>
            <Link className="link-arrow" to="/history">All saved analyses →</Link>
          </div>
        </section>

        <section className="band" aria-labelledby="recent-title" id="recent-analyses">
          <header className="band-head">
            <p className="kicker">Recent</p>
            <h2 id="recent-title">Recent analyses</h2>
            <p>The last eight reports, newest first.</p>
          </header>

          <div className="band-body">
            {loading ? (
              <p className="dash-feedback" role="status">
                Loading your recent analyses…
              </p>
            ) : historyError ? (
              <div className="dash-feedback dash-feedback-error" role="alert">
                <p>{historyError}</p>
                <Link to="/history">Open analysis history</Link>
              </div>
            ) : analyses.length === 0 ? (
              <div className="dash-empty">
                <h3>No analyses yet.</h3>
                <p>
                  Paste a protein sequence or upload a FASTA file to create
                  your first report.
                </p>
                <Link className="btn btn-primary" to="/analyses">
                  Start your first analysis
                </Link>
              </div>
            ) : (
              <table className="ledger recent-table">
                <caption className="visually-hidden">Recent analyses</caption>
                <thead>
                  <tr>
                    <th scope="col">Protein</th>
                    <th scope="col">Organism</th>
                    <th scope="col">Accession</th>
                    <th scope="col">Date</th>
                    <th scope="col">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {analyses.map((analysis) => (
                    <tr key={analysis.analysis_id}>
                      <th scope="row">
                        <Link to={`/analyses/${analysis.analysis_id}`}>
                          {analysis.protein_name || analysis.accession || 'Protein analysis'}
                        </Link>
                      </th>
                      <td data-label="Organism">{analysis.organism || '—'}</td>
                      <td data-label="Accession" className="num">{analysis.accession || '—'}</td>
                      <td data-label="Date" className="num">{formatDate(analysis.created_at)}</td>
                      <td data-label="Status">
                        <span
                          className={`status-tag status-${String(
                            analysis.status || 'unknown',
                          ).toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}
                        >
                          <span aria-hidden="true">{statusMark(analysis.status)}</span>{' '}
                          {formatStatus(analysis.status)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>

        <section className="band" aria-labelledby="flow-title">
          <header className="band-head">
            <p className="kicker">Method</p>
            <h2 id="flow-title">How a run works</h2>
          </header>

          <ol className="band-body flow">
            <li>
              <strong>Submit.</strong> One sequence, or a multi-record FASTA
              file for conservation across strains. Pick a host proteome to
              screen against.
            </li>
            <li>
              <strong>Run.</strong> BLAST, IEDB predictors and structure
              lookup run on background workers; the page updates as results
              arrive.
            </li>
            <li>
              <strong>Review.</strong> Each section lists its evidence, its
              source and its limits. Download the PDF when you are done.
            </li>
          </ol>
        </section>
      </main>

      <footer className="site-footer">
        <p className="wordmark">ReverseVax</p>
        <p>
          Computational research support. Findings require scientific
          evaluation and are not experimental validation.
        </p>
      </footer>
    </div>
  )
}

export default Dashboard
