import { useEffect, useState } from 'react'
import {
  Link,
  Navigate,
  Route,
  Routes,
  useNavigate,
  useParams,
} from 'react-router-dom'

import {
  submitAnalysis,
  submitFastaAnalysis,
  getAnalysisStatus,
  downloadAnalysisReport,
} from './services/analysisService'
import { SESSION_EXPIRED_EVENT } from './services/session'

import AnalysisReport from './components/AnalysisReport'
import AnalysisHistory from './components/AnalysisHistory'
import Register from './components/Register'
import Login from './components/Login'
import MultiSequenceReport from './components/MultiSequenceReport'
import LandingPage from './components/LandingPage'
import Dashboard from './components/Dashboard'
import ThemeToggle from './components/ThemeToggle'
import './App.css'
import './components/AnalysisReport.css'

const ACTIVE_ANALYSIS_KEY = 'activeAnalysisId'

function ProtectedRoute({ authenticated, children }) {
  return authenticated ? children : <Navigate to="/login" replace />
}

function App() {
  const navigate = useNavigate()
  const [authenticated, setAuthenticated] = useState(
    Boolean(localStorage.getItem('token')),
  )

  useEffect(() => {
    function handleSessionExpired() {
      localStorage.removeItem(ACTIVE_ANALYSIS_KEY)
      setAuthenticated(false)
      navigate('/login', { replace: true })
    }

    window.addEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired)

    return () => {
      window.removeEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired)
    }
  }, [navigate])

  return (
    <Routes>
      <Route
        path="/"
        element={
          authenticated ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <LandingPage
              onLogin={() => navigate('/login')}
              onRegister={() => navigate('/register')}
            />
          )
        }
      />

      <Route
        path="/login"
        element={
          authenticated
            ? <Navigate to="/dashboard" replace />
            : <Login onLogin={() => setAuthenticated(true)} />
        }
      />

      <Route
        path="/register"
        element={
          authenticated ? (
            <Navigate to="/dashboard" replace />
          ) : (
            <Register
              onRegister={() => navigate('/login')}
              onLogin={() => navigate('/login')}
            />
          )
        }
      />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute authenticated={authenticated}>
            <Dashboard
              onLogout={() => setAuthenticated(false)}
            />
          </ProtectedRoute>
        }
      />


      <Route
        path="/analyses/:analysisId?"
        element={
          <ProtectedRoute authenticated={authenticated}>
            <AuthenticatedLayout onLogout={() => setAuthenticated(false)}>
              <AnalysisWorkspace />
            </AuthenticatedLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/history"
        element={
          <ProtectedRoute authenticated={authenticated}>
            <AuthenticatedLayout onLogout={() => setAuthenticated(false)}>
              <AnalysisHistory />
            </AuthenticatedLayout>
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function AuthenticatedLayout({ children, onLogout }) {
  const navigate = useNavigate()

  function handleLogout() {
    localStorage.removeItem('token')
    localStorage.removeItem(ACTIVE_ANALYSIS_KEY)
    onLogout()
    navigate('/', { replace: true })
  }

  return (
    <>
      <nav className="app-navigation" aria-label="Main navigation">
        <Link to="/dashboard" className="nav-brand">
          <span className="nav-brand-icon" aria-hidden="true">V</span>
          <span>ReverseVax</span>
        </Link>

        <div className="nav-links">
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/analyses">New analysis</Link>
          <Link to="/history">Analysis history</Link>
          <ThemeToggle />
          <button type="button" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </nav>
      {children}
    </>
  )
}

function AnalysisWorkspace() {
  const { analysisId: routeAnalysisId } = useParams()
  const navigate = useNavigate()

  const [submitted, setSubmitted] = useState(false)
  const [sequence, setSequence] = useState('')
  const [error, setError] = useState(null)
  const [analysisId, setAnalysisId] = useState(routeAnalysisId || '')
  const [status, setStatus] = useState('')
  const [report, setReport] = useState(null)
  const [fastaFile, setFastaFile] = useState(null)
  const [organism, setOrganism] = useState('')
  const [epathGeneId, setEpathGeneId] = useState('')
  const [epathKoId, setEpathKoId] = useState('')
  const [hostReference, setHostReference] = useState('none')


  useEffect(() => {
    setAnalysisId(routeAnalysisId || '')
    setError(null)
  }, [routeAnalysisId])

  useEffect(() => {
    if (!analysisId) return undefined

    let cancelled = false
    let timeoutId

    async function pollAnalysisStatus() {
      try {
        const token = localStorage.getItem('token')

        if (!token) {
          throw new Error('Your session has ended. Please log in again.')
        }

        const result = await getAnalysisStatus(analysisId, token)

        if (cancelled) return

        setStatus(result.status)
        setReport(result.report || null)
        setError(null)

        if (result.status === 'pending' || result.status === 'running') {
          timeoutId = setTimeout(pollAnalysisStatus, 1000)
        }
      } catch (err) {
        if (cancelled) return
        setError(err.message || 'Unable to retrieve analysis status.')
      }
    }

    pollAnalysisStatus()

    return () => {
      cancelled = true
      clearTimeout(timeoutId)
    }
  }, [analysisId])

  async function handleSubmit() {
    setError(null)
    setReport(null)
    setStatus('')
    setSubmitted(false)

    try {
      const token = localStorage.getItem('token')
      if (!token) throw new Error('Please log in before submitting an analysis.')

      let result

      const metadata = {
        organism: organism.trim(),
        epath_gene_id: epathGeneId.trim(),
        epath_ko_id: epathKoId.trim(),
        host_reference: hostReference,
      }

      if (fastaFile) {
        if (!/\.(fasta|fa|fna)$/i.test(fastaFile.name)) {
          setError('Please select a .fasta, .fa, or .fna file.')
          return
        }

        const fastaContent = await fastaFile.text()

        if (!fastaContent.trim()) {
          setError('The selected FASTA file is empty.')
          return
        }

        result = await submitFastaAnalysis(fastaContent, token, metadata)
      } else {
        if (!sequence.trim()) {
          setError('Enter a protein sequence or select a FASTA file.')
          return
        }

        result = await submitAnalysis(sequence, token, metadata)
      }

      if (!result.analysis_id) {
        throw new Error(result.error || 'Unable to submit the analysis.')
      }

      setAnalysisId(result.analysis_id)
      setStatus(result.status || 'pending')
      setReport(result.report || null)
      setSubmitted(true)
      navigate(`/analyses/${result.analysis_id}`)
    } catch (err) {
      setError(err.message || 'Analysis submission failed.')
    }
  }

  async function handleDownloadReport() {
    setError(null)

    try {
      const token = localStorage.getItem('token')
      await downloadAnalysisReport(analysisId, token)
    } catch (err) {
      setError(err.message || 'Unable to download the report.')
    }
  }
  return (
    <main className="analysis-page">
        <header className="workspace-header">
          <p className="eyebrow">PROTEIN ANALYSIS</p>
          <h1>Explore a protein sequence</h1>
          <p>
            Submit a protein sequence or FASTA file to generate computational
            results, evidence, interpretations, and a research report.
          </p>
        </header>

      <div className="analysis-form">
        <label htmlFor="protein-sequence">Protein Sequence</label>
        <p className="input-help" id="protein-sequence-help">
          Paste a single protein sequence using the standard one-letter amino acid codes.
        </p>

        <textarea
          id="protein-sequence"
          name="protein-sequence"
          aria-describedby="protein-sequence-help"
          value={sequence}
          onChange={(event) => setSequence(event.target.value)}
        />

        <section className="analysis-metadata-fields" aria-labelledby="metadata-heading">
          <h2 id="metadata-heading">Reference Metadata</h2>

          <p className="input-help">
            These fields are optional. Provide identifiers only when you know they
            correspond to the selected organism and the ePath reference data.
          </p>

          <label htmlFor="organism">Organism</label>
          <input
            id="organism"
            name="organism"
            type="text"
            value={organism}
            onChange={(event) => setOrganism(event.target.value)}
            placeholder="e.g. Escherichia coli K-12 MG1655"
          />

          <label htmlFor="host-reference">Host Similarity Reference</label>
          <select
            id="host-reference"
            name="host_reference"
            value={hostReference}
            onChange={(event) => setHostReference(event.target.value)}
            aria-describedby="host-reference-help"
          >
            <option value="none">None (skip host similarity search)</option>
            <option value="human">Human</option>
            <option value="mouse">Mouse</option>
            <option value="pig">Pig</option>
          </select>

          <p className="input-help" id="host-reference-help">
            Select the host proteome to use for similarity analysis.
            Choose None to skip host similarity searching.
          </p>

          <label htmlFor="epath-gene-id">ePath Gene ID</label>
          <input
            id="epath-gene-id"
            name="epath-gene-id"
            type="text"
            value={epathGeneId}
            onChange={(event) => setEpathGeneId(event.target.value)}
            placeholder="Optional gene identifier"
          />

          <label htmlFor="epath-ko-id">ePath KO ID</label>
          <input
            id="epath-ko-id"
            name="epath-ko-id"
            type="text"
            value={epathKoId}
            onChange={(event) => setEpathKoId(event.target.value)}
            placeholder="Optional KO identifier"
          />
        </section>

        <label htmlFor="fasta-file">Upload FASTA File</label>
        <p className="input-help" id="fasta-file-help">
          Alternatively, upload a .fasta, .fa, or .fna file. Multiple FASTA records
          can be analyzed together.
        </p>

        <input
          id="fasta-file"
          name="fasta-file"
          type="file"
          accept=".fasta,.fa,.fna"
          onChange={(event) => setFastaFile(event.target.files?.[0] ?? null)}
        />

        {fastaFile && <p>Selected file: {fastaFile.name}</p>}

        <button type="button" className="analysis-submit" onClick={handleSubmit}>
          Analyze Protein
        </button>
      </div>

      {report && (
        <>
          {Array.isArray(report.alignment) && Array.isArray(report.records)
            ? <MultiSequenceReport report={report} />
            : <AnalysisReport report={report} />}

          {status === 'completed' && (
            <button
              type="button"
              className="analysis-submit"
              onClick={handleDownloadReport}
            >
              Download PDF Report
            </button>
          )}
        </>
      )}

      {(status || submitted || error) && (
        <section
          className={`analysis-status-panel ${
            error || status === 'failed'
              ? 'status-failed'
              : status === 'completed'
                ? 'status-completed'
                : 'status-in-progress'
          }`}
          aria-live="polite"
          aria-atomic="true"
        >
          <div className="status-heading">
            <span className="status-indicator" aria-hidden="true">
              {status === 'completed' ? '✓' : error || status === 'failed' ? '!' : ''}
            </span>

            <div className="status-copy">
              <h3>
                {error || status === 'failed'
                  ? 'Analysis failed'
                  : status === 'completed'
                    ? 'Analysis completed'
                    : status === 'running'
                      ? 'Analysis in progress'
                      : status === 'pending'
                        ? 'Analysis queued'
                        : 'Submitting analysis'}
              </h3>

              <p>
                {error
                  ? error
                  : status === 'failed'
                    ? 'The analysis could not be completed. Please try again.'
                    : status === 'completed'
                      ? 'Your results are ready to review.'
                      : status === 'running'
                        ? 'Your protein sequence is being analyzed. This may take a little while.'
                        : 'Your request has been received and is waiting to be processed.'}
              </p>
            </div>

            {(status === 'pending' || status === 'running' || (!status && submitted)) && (
              <span className="status-spinner" aria-hidden="true" />
            )}
          </div>

          {analysisId && (
            <div className="status-id">
              <span>Analysis ID</span>
              <code>{analysisId}</code>
              <button
                type="button"
                className="copy-analysis-id"
                onClick={() => navigator.clipboard?.writeText(analysisId)}
                aria-label="Copy analysis ID"
                title="Copy analysis ID"
              >
                Copy
              </button>
            </div>
          )}
        </section>
      )}
    </main>
  )
}

export default App

