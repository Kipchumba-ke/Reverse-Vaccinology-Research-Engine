import './HeroSlides.css'

// Background slideshow for the hero blocks on the landing page and the
// dashboard. Pure presentation: three photographs cross-fade in CSS, sit under
// a dark scrim so the text stays readable, and are hidden from assistive
// technology. The image addresses are in HeroSlides.css.
function HeroSlides() {
  return (
    <>
      <div className="hero-slides" aria-hidden="true">
        <span className="hero-slide hero-slide-1" />
        <span className="hero-slide hero-slide-2" />
        <span className="hero-slide hero-slide-3" />
        <span className="hero-scrim" />
      </div>
      <p className="hero-credit">
        Photos: digitale.de, Terry Vlisidis and Sangharsh Lohakare on{' '}
        <a href="https://unsplash.com" target="_blank" rel="noreferrer">
          Unsplash
        </a>
      </p>
    </>
  )
}

export default HeroSlides
