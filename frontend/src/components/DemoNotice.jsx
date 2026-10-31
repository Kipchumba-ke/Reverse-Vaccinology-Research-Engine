import './DemoNotice.css'

// A notice for a public, interface-only deployment (for example a portfolio
// site on Netlify with no analysis server behind it). It is off unless the
// site is built with VITE_DEMO_NOTICE=true, so a real deployment and local
// development never show it.
//
// VITE_DEMO_VIDEO_URL is optional: the address of a screen recording. It is
// ignored unless it starts with https://.

const REPOSITORY_URL =
  'https://github.com/Kipchumba-ke/reverse-vaccinology-research-engine'

// Read when rendered, not when the file loads, so tests can change them.
export function isDemoSite() {
  return import.meta.env?.VITE_DEMO_NOTICE === 'true'
}

function videoUrl() {
  const url = import.meta.env?.VITE_DEMO_VIDEO_URL
  return typeof url === 'string' && url.startsWith('https://') ? url : null
}

function DemoNotice() {
  if (!isDemoSite()) return null

  const video = videoUrl()

  return (
    <aside className="demo-notice" aria-label="About this demo site">
      <p className="demo-notice-title">Portfolio demo: interface only</p>
      <p className="demo-notice-text">
        The analysis server is not hosted online, so signing in, registering
        and running analyses are switched off on this site. The full tool runs
        locally.
        {video && ' A screen recording shows it working end to end.'}
      </p>
      <p className="demo-notice-links">
        {video && (
          <a href={video} target="_blank" rel="noopener noreferrer">
            Watch the 2–3 minute demo
          </a>
        )}
        <a href={REPOSITORY_URL} target="_blank" rel="noopener noreferrer">
          Read the code on GitHub
        </a>
      </p>
    </aside>
  )
}

export default DemoNotice
