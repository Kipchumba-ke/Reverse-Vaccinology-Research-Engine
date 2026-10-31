import ThemeToggle from './ThemeToggle'
import DemoNotice from './DemoNotice'
import { EvidenceStory, ExampleFigure, SourcesList } from './EvidenceStory'
import './Shell.css'
import './LandingPage.css'

// Set VITE_CONTACT_EMAIL at build time to show a contact address for
// investors and partners. Nothing is shown when it is not configured.
const CONTACT_EMAIL = import.meta.env?.VITE_CONTACT_EMAIL

function LandingPage({ onLogin, onRegister }) {
  return (
    <div className="landing-page shell" id="top">
      <a className="skip-link" href="#main">Skip to main content</a>
      <header className="site-header">
        <div className="site-header-inner">
          <a className="wordmark" href="#top">
            ReverseVax
            <span>evidence ledger for vaccine-target discovery</span>
          </a>

          <nav className="site-nav" aria-label="Main navigation">
            <a href="#problem">Problem</a>
            <a href="#method">Method</a>
            <a href="#paths">Who it is for</a>
            <a href="#standards">Evidence standard</a>
          </nav>

          <div className="site-actions">
            <ThemeToggle />
            <button type="button" className="btn btn-quiet" onClick={onLogin}>
              Sign in
            </button>
            <button type="button" className="btn btn-primary" onClick={onRegister}>
              Get started
            </button>
          </div>
        </div>
      </header>

      <DemoNotice />

      <main id="main" className="sections">
        <section className="hero" aria-labelledby="hero-title">
          <p className="kicker">Reverse vaccinology · research prototype</p>
          <h1 id="hero-title">Shortlist vaccine targets with evidence you can audit.</h1>
          <p className="lede">
            A pathogen’s genome encodes thousands of proteins; a lab can test
            only a handful. ReverseVax reads a protein sequence and returns a
            sourced report on whether it is a promising target.
          </p>
          <p className="lede-note">
            Every claim in the report carries its source, its confidence and
            its limits.
          </p>
          <div className="hero-actions">
            <button type="button" className="btn btn-primary" onClick={onRegister}>
              Get started
            </button>
            <a className="link-arrow" href="#method">
              See how a report is built →
            </a>
          </div>
        </section>

        <section className="hero-evidence" aria-labelledby="figure-heading">
          <h2 id="figure-heading" className="visually-hidden">
            An example report figure and the sources it is built on
          </h2>
          <figure className="hero-figure">
            <p className="kicker">Fig. 1</p>
            <ExampleFigure />
            <figcaption>
              Sequence map, in the format ReverseVax produces. Example data
              for illustration, not a real result.
            </figcaption>
          </figure>

          <div className="hero-sources">
            <p className="kicker">Built on</p>
            <SourcesList />
          </div>
        </section>

        <EvidenceStory
          primaryAction={
            <button type="button" className="btn btn-primary" onClick={onRegister}>
              Get started
            </button>
          }
        />
      </main>

      <footer className="site-footer">
        <p className="wordmark">ReverseVax</p>
        <p>
          Computational research support. Findings require scientific
          evaluation and are not experimental validation.
        </p>
        {CONTACT_EMAIL && (
          <p>
            Investors and partners: <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
          </p>
        )}
      </footer>
    </div>
  )
}

export default LandingPage
