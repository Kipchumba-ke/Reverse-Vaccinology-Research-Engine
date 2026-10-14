
import './LandingPage.css'

function LandingPage({ onLogin, onRegister }) {
  return (
    <main className="landing-page">
      <header className="landing-nav">
        <a className="landing-brand" href="#home" aria-label="ReverseVax home">
          <span className="landing-brand-icon" aria-hidden="true">R</span>
          <span>
            <strong>ReverseVax</strong>
            <small>RESEARCH ENGINE</small>
          </span>
        </a>

        <nav className="landing-nav-links" aria-label="Main navigation">
          <a href="#platform">Platform</a>
          <a href="#workflow">Workflow</a>
          <a href="#about">About</a>
        </nav>

        <div className="landing-nav-actions">
          <button className="landing-signin" onClick={onLogin}>
            Sign in
          </button>
          <button className="landing-nav-cta" onClick={onRegister}>
            Get started <span aria-hidden="true">↗</span>
          </button>
        </div>
      </header>

      <section className="landing-hero" id="home">
        <div className="landing-hero-content">
          <div className="landing-eyebrow">
            <span className="landing-status-dot" />
            COMPUTATIONAL BIOLOGY · RESEARCH
          </div>

          <h1>
            From protein sequences
            <br />
            to <span>research insights.</span>
          </h1>

          <p className="landing-hero-description">
            Explore pathogen proteins through computational analysis,
            sequence comparison, and explainable research reports.
            Turn complex biological data into findings you can investigate.
          </p>

          <div className="landing-hero-actions">
            <button className="landing-primary-button" onClick={onRegister}>
              Start exploring <span aria-hidden="true">→</span>
            </button>
            <a className="landing-secondary-button" href="#workflow">
              Explore the workflow
            </a>
          </div>

          <div className="landing-trust-note">
            <span aria-hidden="true">✓</span>
            Computational evidence, transparent limitations
          </div>
        </div>

        <div className="landing-visual" aria-label="Illustration of a protein analysis workflow">
          <div className="landing-visual-orbit landing-orbit-one" />
          <div className="landing-visual-orbit landing-orbit-two" />

          <div className="landing-molecule">
            <svg viewBox="0 0 320 320" role="img" aria-label="Abstract protein structure illustration">
              <defs>
                <linearGradient id="proteinGradient" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stopColor="#B9F3D3" />
                  <stop offset="100%" stopColor="#51B58C" />
                </linearGradient>
              </defs>

              <g fill="none" stroke="url(#proteinGradient)" strokeWidth="5" strokeLinecap="round">
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
            <span className="landing-float-icon">⌘</span>
            <span>
              <strong>Sequence analysis</strong>
              <small>Protein characteristics</small>
            </span>
          </div>

          <div className="landing-float-card landing-float-bottom">
            <span className="landing-float-icon">↗</span>
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

      <section className="landing-features" id="platform">
        <div className="landing-section-heading">
          <span>THE PLATFORM</span>
          <h2>Make biological analysis easier to explore.</h2>
          <p>
            Bring sequence analysis, comparative insights, and scientific
            interpretation together in one research workflow.
          </p>
        </div>

        <div className="landing-feature-grid">
          <article className="landing-feature-card">
            <div className="landing-feature-icon">01</div>
            <h3>Analyze sequences</h3>
            <p>
              Examine protein characteristics, hydropathy profiles,
              hydrophobic regions, and transmembrane candidates.
            </p>
          </article>

          <article className="landing-feature-card">
            <div className="landing-feature-icon">02</div>
            <h3>Compare proteins</h3>
            <p>
              Explore multiple-sequence alignments and per-position
              majority-residue frequency when comparative sequences are available.
            </p>
          </article>

          <article className="landing-feature-card">
            <div className="landing-feature-icon">03</div>
            <h3>Interpret findings</h3>
            <p>
              Review computational evidence alongside explanations,
              uncertainty, and research limitations.
            </p>
          </article>
        </div>
      </section>

      <section className="landing-workflow" id="workflow">
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

      <section className="landing-final-cta" id="about">
        <div>
          <span className="landing-section-label">READY TO EXPLORE?</span>
          <h2>Start with a sequence. Follow the evidence.</h2>
          <p>
            Investigate computational results while keeping their
            assumptions and limitations in view.
          </p>
        </div>

        <button className="landing-primary-button" onClick={onRegister}>
          Get started <span aria-hidden="true">→</span>
        </button>
      </section>

      <footer className="landing-footer">
        <a className="landing-brand landing-footer-brand" href="#home">
          <span className="landing-brand-icon" aria-hidden="true">R</span>
          <span>
            <strong>ReverseVax</strong>
            <small>RESEARCH ENGINE</small>
          </span>
        </a>
        <p>
          Computational research support. Findings require scientific
          evaluation and are not experimental validation.
        </p>
      </footer>
    </main>
  )
}

export default LandingPage
