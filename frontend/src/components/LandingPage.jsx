import ThemeToggle from './ThemeToggle'
import './Shell.css'
import './LandingPage.css'

// Set VITE_CONTACT_EMAIL at build time to show a contact address for
// investors and partners. Nothing is shown when it is not configured.
const CONTACT_EMAIL = import.meta.env?.VITE_CONTACT_EMAIL

// Example data for Figure 1. It is invented, and labelled as such on the page.
const FIGURE_LENGTH = 312
const FIGURE_LANES = [
  { label: 'Signal peptide', color: '#0072B2', spans: [[1, 24]] },
  { label: 'Transmembrane', color: '#D55E00', spans: [[148, 170], [196, 218]] },
  { label: 'Antigenic region', color: '#009E73', spans: [[34, 62], [94, 121], [236, 270]] },
  { label: 'B-cell epitope', color: '#CC79A7', spans: [[100, 118], [240, 262]] },
  { label: 'MHC-I binder', color: '#56B4E9', spans: [[96, 104], [243, 251], [255, 263]] },
]

const SOURCES = [
  ['NCBI BLAST+', 'similarity to host proteins'],
  ['IEDB Analysis Resource', 'MHC-I, MHC-II and BepiPred-2.0 B-cell predictions'],
  ['AlphaFold DB', 'predicted 3-D models'],
  ['Kolaskar–Tongaonkar', 'antigenic propensity scale'],
  ['DeepTMHMM · PSORTb · SignalP', 'optional, imported when you supply their output'],
]

const QUESTIONS = [
  {
    question: 'Is it on the pathogen’s surface?',
    method: 'Signal-peptide and transmembrane screens; localization evidence you import from DeepTMHMM, PSORTb or SignalP.',
    source: 'ReverseVax rules; optional external tools',
    limit: 'The built-in screens are heuristics, not those tools’ output, and are labelled as such.',
  },
  {
    question: 'Does it resemble a host protein?',
    method: 'BLAST search against the human, mouse or pig proteome, with identity, coverage and e-value for each hit.',
    source: 'NCBI BLAST+',
    limit: 'Similarity thresholds are provisional screening conventions, not validated cut-offs.',
  },
  {
    question: 'Could immune cells recognise parts of it?',
    method: 'Antigenic-propensity windows; MHC class I and II binding for a fixed allele panel; linear B-cell epitopes.',
    source: 'Kolaskar–Tongaonkar; IEDB Analysis Resource',
    limit: 'Binding is not processing, presentation or immunogenicity.',
  },
  {
    question: 'Is it shared across strains?',
    method: 'Per-position conservation from a multiple-sequence alignment you provide.',
    source: 'Your FASTA alignment',
    limit: 'Only as good as the alignment and the strains you choose.',
  },
  {
    question: 'What does it look like in 3-D?',
    method: 'Fetches the AlphaFold model for the UniProt accession, coloured by model confidence or by predicted features.',
    source: 'AlphaFold Protein Structure Database',
    limit: 'A predicted model, not an experimental structure; low-confidence regions are flagged.',
  },
]

function ExampleFigure() {
  const width = 560
  const left = 118
  const right = 12
  const rowHeight = 30
  const top = 14
  const plot = width - left - right
  const x = (position) => left + ((position - 1) / (FIGURE_LENGTH - 1)) * plot
  const height = top + FIGURE_LANES.length * rowHeight + 34

  return (
    <svg
      className="figure-svg"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-labelledby="figure-1-title figure-1-desc"
    >
      <title id="figure-1-title">Example sequence map</title>
      <desc id="figure-1-desc">
        Five labelled lanes along a 312-residue example protein: a signal
        peptide at the start, two transmembrane segments near the middle,
        three antigenic regions, two B-cell epitopes and three MHC class I
        binders. The data are invented for illustration.
      </desc>

      {FIGURE_LANES.map((lane, index) => {
        const y = top + index * rowHeight
        return (
          <g key={lane.label}>
            <text x={left - 10} y={y + 14} textAnchor="end" className="figure-label">
              {lane.label}
            </text>
            <line x1={left} x2={left + plot} y1={y + 10} y2={y + 10} className="figure-lane" />
            {lane.spans.map(([start, end]) => (
              <rect
                key={`${start}-${end}`}
                x={x(start)}
                y={y + 3}
                width={Math.max(3, x(end) - x(start))}
                height="14"
                fill={lane.color}
                className="figure-bar"
              >
                <title>{`${lane.label}, residues ${start}–${end}`}</title>
              </rect>
            ))}
          </g>
        )
      })}

      {[1, 78, 156, 234, 312].map((tick) => (
        <g key={tick}>
          <line
            x1={x(tick)}
            x2={x(tick)}
            y1={top + FIGURE_LANES.length * rowHeight + 2}
            y2={top + FIGURE_LANES.length * rowHeight + 8}
            className="figure-axis"
          />
          <text
            x={x(tick)}
            y={top + FIGURE_LANES.length * rowHeight + 22}
            textAnchor="middle"
            className="figure-tick"
          >
            {tick}
          </text>
        </g>
      ))}
    </svg>
  )
}

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

      <main id="main">
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-copy">
            <p className="kicker">Reverse vaccinology · research prototype</p>
            <h1 id="hero-title">Shortlist vaccine targets with evidence you can audit.</h1>
            <p className="lede">
              A pathogen’s genome encodes thousands of proteins; a lab can
              test only a handful. ReverseVax reads a protein sequence and
              returns a sourced report on whether it is a promising target,
              with every claim’s source, confidence and limits written beside it.
            </p>
            <div className="hero-actions">
              <button type="button" className="btn btn-primary" onClick={onRegister}>
                Get started
              </button>
              <a className="link-arrow" href="#method">
                See how a report is built →
              </a>
            </div>
          </div>

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
            <ul>
              {SOURCES.map(([name, role]) => (
                <li key={name}>
                  <strong>{name}</strong>
                  <span>{role}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="story" id="problem" aria-labelledby="problem-title">
          <h2 id="problem-title" className="visually-hidden">
            The problem, and what ReverseVax does about it
          </h2>
          <div className="story-part story-problem">
            <p className="kicker">1 · The problem</p>
            <p>
              Testing every protein from a new pathogen at the bench is not
              practical, and a wrong pick costs time a lab rarely has.
            </p>
          </div>
          <div className="story-part story-target">
            <p className="kicker">2 · A good target…</p>
            <p>
              sits on the pathogen’s surface, looks nothing like a host
              protein, is shared across strains, and has parts that immune
              cells can recognise.
            </p>
          </div>
          <div className="story-part story-answer">
            <p className="kicker">3 · ReverseVax</p>
            <p>
              checks each of those from the sequence, names the tool behind
              every answer, and lists what is still missing.
            </p>
          </div>
        </section>

        <section className="band" id="method" aria-labelledby="method-title">
          <header className="band-head">
            <p className="kicker">Method</p>
            <h2 id="method-title">Five questions, one report.</h2>
            <p>
              Each question is answered by a named method, shown with its
              source, and paired with the limit a reader should keep in mind.
            </p>
          </header>

          <div className="band-body">
            <table className="ledger">
              <caption className="visually-hidden">
                Questions a ReverseVax report answers, with method, source and stated limit
              </caption>
              <thead>
                <tr>
                  <th scope="col">Question</th>
                  <th scope="col">How it is answered</th>
                  <th scope="col">Source</th>
                  <th scope="col">Stated limit</th>
                </tr>
              </thead>
              <tbody>
                {QUESTIONS.map((row) => (
                  <tr key={row.question}>
                    <th scope="row">{row.question}</th>
                    <td data-label="How it is answered">{row.method}</td>
                    <td data-label="Source">{row.source}</td>
                    <td data-label="Stated limit" className="ledger-limit">{row.limit}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="band" id="paths" aria-labelledby="paths-title">
          <header className="band-head">
            <p className="kicker">Who it is for</p>
            <h2 id="paths-title">Three readers, three starting points.</h2>
          </header>

          <div className="band-body paths">
            <article className="path path-researchers" aria-labelledby="path-researchers">
              <h3 id="path-researchers">Researchers</h3>
              <p className="path-ask">Which of my candidate proteins should go to the bench first?</p>
              <ul>
                <li>Paste one sequence or upload a multi-record FASTA file.</li>
                <li>Read the evidence report, with limitations listed for each result.</li>
                <li>Magnify any chart, compare conservation, and export the report as a PDF.</li>
                <li>Reopen earlier analyses from your history.</li>
              </ul>
              <button type="button" className="btn btn-primary" onClick={onRegister}>
                Get started
              </button>
            </article>

            <article className="path" aria-labelledby="path-investors">
              <h3 id="path-investors">Investors</h3>
              <p className="path-ask">What exists today, and how far can it be trusted?</p>
              <ul>
                <li>A working pipeline from sequence to report, covered by automated tests.</li>
                <li>Prediction sources are named; results are screens, not validation.</li>
                <li>No benchmark results are published yet.</li>
              </ul>
              <a className="link-arrow" href="#standards">Read the evidence standard →</a>
            </article>

            <article className="path" aria-labelledby="path-partners">
              <h3 id="path-partners">Commercial partners</h3>
              <p className="path-ask">Can it run on our data, with our licensed tools?</p>
              <ul>
                <li>Self-hosted with Docker Compose; analyses run on background workers.</li>
                <li>REST API for submitting sequences and fetching reports.</li>
                <li>DeepTMHMM, PSORTb and SignalP output can be imported if you hold the licence.</li>
              </ul>
              <a className="link-arrow" href="#standards">How claims are bounded →</a>
            </article>
          </div>
        </section>

        <section className="band" id="standards" aria-labelledby="standards-title">
          <header className="band-head">
            <p className="kicker">Evidence standard</p>
            <h2 id="standards-title">What we claim, and what we do not.</h2>
          </header>

          <div className="band-body standards">
            <div>
              <h3>We claim</h3>
              <ul>
                <li>Each result is traceable to a named method or database.</li>
                <li>Our own rule-based screens are labelled as ours, never as SignalP, TMHMM or BepiPred output.</li>
                <li>Missing evidence is listed in the report, not hidden.</li>
                <li>Every report ends with its limitations.</li>
              </ul>
            </div>
            <div className="standards-not">
              <h3>We do not claim</h3>
              <ul>
                <li>That a candidate is immunogenic, protective or safe.</li>
                <li>That low similarity to the host proves safety.</li>
                <li>That predictions replace laboratory work.</li>
                <li>Benchmarked accuracy: none is published yet.</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="band" id="responsible" aria-labelledby="responsible-title">
          <header className="band-head">
            <p className="kicker">Responsible and accessible</p>
            <h2 id="responsible-title">Built to be read by everyone.</h2>
          </header>

          <div className="band-body standards">
            <div>
              <h3>Accessibility</h3>
              <ul>
                <li>Keyboard operable throughout, with a visible focus ring.</li>
                <li>Text contrast of at least 4.5:1 in both light and dark themes.</li>
                <li>Charts have labelled lanes, text alternatives and zoom controls.</li>
                <li>Animation respects your reduced-motion setting.</li>
              </ul>
            </div>
            <div>
              <h3>Your data</h3>
              <ul>
                <li>Sequences are stored with your account so you can reopen reports.</li>
                <li>You can delete any analysis from Analysis history.</li>
                <li>No advertising or tracking scripts.</li>
              </ul>
            </div>
          </div>
        </section>
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
