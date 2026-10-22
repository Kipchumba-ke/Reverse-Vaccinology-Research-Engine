import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getAnalysisHistory } from '../services/historyService'
import './LandingPage.css'
import './Dashboard.css'

const ACTIVE_ANALYSIS_KEY = 'activeAnalysisId'

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
          setAnalyses(Array.isArray(results) ? results.slice(0, 5) : [])
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

    return status.replace(/[_-]+/g, ' ')
  }

  return (
    <main className="landing-page dashboard-page">
      <header className="landing-nav dashboard-nav">
        <Link
          className="landing-brand"
          to="/dashboard"
          aria-label="ReverseVax dashboard"
        >
          <span className="landing-brand-icon" aria-hidden="true">R</span>
          <span>
            <strong>ReverseVax</strong>
            <small>RESEARCH ENGINE</small>
          </span>
        </Link>

        <nav className="landing-nav-links" aria-label="Main navigation">
          <Link className="dashboard-nav-active" to="/dashboard">
            Dashboard
          </Link>
          <Link to="/analyses">New analysis</Link>
          <Link to="/history">Analysis history</Link>
        </nav>

        <div className="landing-nav-actions">
          <button
            className="dashboard-logout"
            type="button"
            onClick={handleLogout}
          >
            Log out
          </button>
          <Link className="landing-nav-cta" to="/analyses">
            New analysis <span aria-hidden="true">↗</span>
          </Link>
        </div>
      </header>

      <section className="landing-hero dashboard-hero" id="home">
        <div className="landing-hero-content">
          <div className="landing-eyebrow">
            <span className="landing-status-dot" />
            YOUR RESEARCH WORKSPACE
          </div>

          <h1>
            From protein sequences
            <br />
            to <span>research insights.</span>
          </h1>

          <p className="landing-hero-description">
            Welcome to your ReverseVax workspace. Start a new protein
            analysis, revisit previous findings, and explore computational
            evidence with its interpretation and limitations.
          </p>

          <div className="landing-hero-actions">
            <Link className="landing-primary-button" to="/analyses">
              New analysis <span aria-hidden="true">→</span>
            </Link>
            <Link className="landing-secondary-button" to="/history">
              View analysis history
            </Link>
          </div>

          <div className="landing-trust-note">
            <span aria-hidden="true">✓</span>
            Computational evidence, transparent limitations
          </div>
        </div>

        <div
          className="landing-visual"
          aria-label="Illustration of a protein analysis workflow"
        >
          <div className="landing-visual-orbit landing-orbit-one" />
          <div className="landing-visual-orbit landing-orbit-two" />

          <div className="landing-molecule">
            <svg
              viewBox="0 0 320 320"
              role="img"
              aria-label="Abstract protein structure illustration"
            >
              <defs>
                <linearGradient
                  id="dashboardProteinGradient"
                  x1="0"
                  y1="0"
                  x2="1"
                  y2="1"
                >
                  <stop offset="0%" stopColor="#B9F3D3" />
                  <stop offset="100%" stopColor="#51B58C" />
                </linearGradient>
              </defs>

              <g
                fill="none"
                stroke="url(#dashboardProteinGradient)"
                strokeWidth="5"
                strokeLinecap="round"
              >
                <path d="M160 38 L206 62 L226 104 L202 135 L242 166 L219 208 L178 221 L158 272" />
                <path d="M160 38 L118 69 L92 107 L111 146 L76 179 L96 217 L139 235 L158 272" />
                <path d="M118 69 L172 94 L226 104" />
                <path d="M111 146 L164 155 L202 135" />
                <path d="M76 179 L135 188 L219 208" />
                <path d="M139 235 L178 221 L242 166" />
                <path d="M92 107 L148 119 L172 94" />
                <path d="M164 155 L135 188 L139 235" />
              </g>

              <g fill="#D7F8E5" stroke="#176B4B" strokeWidth="2">
                {[
                  [160, 38], [206, 62], [226, 104], [202, 135],
                  [242, 166], [219, 208], [178, 221], [158, 272],
                  [139, 235], [96, 217], [76, 179], [111, 146],
                  [92, 107], [118, 69], [172, 94], [164, 155],
                  [135, 188],
                ].map(([cx, cy]) => (
                  <circle key={`${cx}-${cy}`} cx={cx} cy={cy} r="7" />
                ))}
              </g>
            </svg>
          </div>

          <div className="landing-float-card landing-float-top">
            <span className="landing-float-icon" aria-hidden="true">⌘</span>
            <span>
              <strong>Sequence analysis</strong>
              <small>Protein characteristics</small>
            </span>
          </div>

          <div className="landing-float-card landing-float-bottom">
            <span className="landing-float-icon" aria-hidden="true">↗</span>
            <span>
              <strong>Research insights</strong>
              <small>Evidence and interpretation</small>
            </span>
          </div>

          <div className="landing-visual-caption">
            <span className="landing-status-dot" />
            COMPUTATIONAL ANALYSIS WORKFLOW
          </div>
        </div>
      </section>

      <section className="landing-features dashboard-features" id="platform">
        <div className="landing-section-heading">
          <span>YOUR WORKSPACE</span>
          <h2>Everything you need to explore your analyses.</h2>
          <p>
            Start an analysis, compare available sequences, and revisit
            previous reports from one place.
          </p>
        </div>

        <div className="landing-feature-grid">
          <article className="landing-feature-card">
            <div className="landing-feature-icon">01</div>
            <h3>New analysis</h3>
            <p>
              Submit a protein sequence and explore its computational
              characteristics and analysis report.
            </p>
            <Link className="dashboard-card-link" to="/analyses">
              Start an analysis <span aria-hidden="true">→</span>
            </Link>
          </article>

          <article className="landing-feature-card">
            <div className="landing-feature-icon">02</div>
            <h3>Analysis history</h3>
            <p>
              Reopen previous analyses and follow your research work
              without resubmitting the same sequence.
            </p>
            <Link className="dashboard-card-link" to="/history">
              View history <span aria-hidden="true">→</span>
            </Link>
          </article>

          <article className="landing-feature-card">
            <div className="landing-feature-icon">03</div>
            <h3>Explainable findings</h3>
            <p>
              Review computational evidence alongside its interpretation,
              uncertainty, and research limitations.
            </p>
            <a className="dashboard-card-link" href="#recent-analyses">
              Recent analyses <span aria-hidden="true">↓</span>
            </a>
          </article>
        </div>
      </section>

      <section className="dashboard-recent" id="recent-analyses">
        <div className="dashboard-section-heading">
          <div>
            <span className="landing-section-label">YOUR RESEARCH ACTIVITY</span>
            <h2>Recent analyses</h2>
            <p>Return to a previous analysis or start a new one.</p>
          </div>

          <Link className="dashboard-history-link" to="/history">
            View all history <span aria-hidden="true">→</span>
          </Link>
        </div>

        {loading ? (
          <p className="dashboard-feedback" role="status">
            Loading your recent analyses…
          </p>
        ) : historyError ? (
          <div className="dashboard-feedback dashboard-feedback-error" role="alert">
            <p>{historyError}</p>
            <Link to="/history">Open analysis history</Link>
          </div>
        ) : analyses.length === 0 ? (
          <div className="dashboard-empty-state">
            <span className="dashboard-empty-icon" aria-hidden="true">+</span>
            <h3>Your research starts here</h3>
            <p>
              You have no saved analyses yet. Submit a protein sequence
              to create your first report.
            </p>
            <Link className="landing-primary-button" to="/analyses">
              Start your first analysis <span aria-hidden="true">→</span>
            </Link>
          </div>
        ) : (
          <div className="dashboard-analysis-list">
            {analyses.map((analysis) => (
              <Link
                className="dashboard-analysis-item"
                key={analysis.analysis_id}
                to={`/analyses/${analysis.analysis_id}`}
              >
                <span className="dashboard-analysis-mark" aria-hidden="true">
                  R
                </span>

                <span className="dashboard-analysis-info">
                  <strong>
                    {analysis.protein_name || analysis.accession || 'Protein analysis'}
                  </strong>
                  <small>
                    {[
                      analysis.organism,
                      analysis.accession,
                      formatDate(analysis.created_at),
                    ].filter(Boolean).join(' · ')}
                  </small>
                </span>

                <span
                  className={`dashboard-analysis-status status-${String(
                    analysis.status || 'unknown',
                  ).toLowerCase().replace(/[^a-z0-9]+/g, '-')}`}
                >
                  {formatStatus(analysis.status)}
                </span>

                <span className="dashboard-analysis-arrow" aria-hidden="true">
                  →
                </span>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section className="landing-workflow dashboard-workflow" id="workflow">
        <div>
          <span className="landing-section-label">A CLEARER WORKFLOW</span>
          <h2>From input to an explainable report.</h2>
        </div>

        <div className="landing-workflow-steps">
          <div><span>01</span><strong>Submit a sequence</strong></div>
          <div><span>02</span><strong>Run the analysis</strong></div>
          <div><span>03</span><strong>Review the findings</strong></div>
        </div>
      </section>

      <section className="landing-final-cta dashboard-final-cta" id="about">
        <div>
          <span className="landing-section-label">READY TO EXPLORE?</span>
          <h2>Start with a sequence. Follow the evidence.</h2>
          <p>
            Investigate computational results while keeping their
            assumptions and limitations in view.
          </p>
        </div>

        <Link className="landing-primary-button" to="/analyses">
          New analysis <span aria-hidden="true">→</span>
        </Link>
      </section>

      <footer className="landing-footer">
        <Link
          className="landing-brand landing-footer-brand"
          to="/dashboard"
          aria-label="ReverseVax dashboard"
        >
          <span className="landing-brand-icon" aria-hidden="true">R</span>
          <span>
            <strong>ReverseVax</strong>
            <small>RESEARCH ENGINE</small>
          </span>
        </Link>
        <p>
          Computational research support. Findings require scientific
          evaluation and are not experimental validation.
        </p>
      </footer>
    </main>
  )
}

export default Dashboard