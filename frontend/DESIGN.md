# ReverseVax — design brief

## Concept: the evidence ledger

ReverseVax does not predict that a protein is a good vaccine target. It
*compiles evidence* — where a protein sits, whether it resembles the host,
which parts the immune system could see — and records, next to each claim,
where it came from and what it cannot show. The interface is therefore
designed as a **ledger / lab notebook / journal figure**, not a SaaS dashboard.

What that means in practice:

- **Warm paper and ink.** Off-white page, near-black text, hairline rules.
  Dark mode is a warm charcoal in the family of Claude's own dark theme, not a
  blue-black or a green-black.
- **Rules instead of cards.** Sections are separated by 1px rules and a
  numbered margin, the way a printed paper is. No floating cards, shadows,
  glass, gradients or pill buttons. Corners are 2px.
- **Everything is a figure or a table.** Numbers are set in tabular mono,
  charts have captions ("Fig. 2") and can be magnified, tables are ruled.
- **The accent is the reviewer's red pen.** One colour, used for the things a
  reader must not miss: the primary action, selected evidence, limitations.
  Status is never colour alone.

## Audience and first impression

Primary reader: a researcher or student in microbiology, immunology or public
health who must decide *which proteins go to the bench*. Secondary readers:
investors and commercial partners who need to see, quickly, what is real, how
it is validated, and what is not claimed.

First viewport: the claim ("Shortlist vaccine targets with evidence you can
audit"), the problem and method in three short statements, a labelled example
figure, and the named sources the pipeline relies on. No stock imagery, no
invented customers, no invented metrics.

## Type

| Role | Family | Use |
| --- | --- | --- |
| Text and headings | Source Serif 4 | Reading text, headings, pull statements |
| Interface | IBM Plex Sans | Navigation, buttons, labels, tables |
| Data | IBM Plex Mono | Sequences, identifiers, figures, kickers |

Scale (≈1.25): 12 · 14 · 17 · 21 · 27 · 34 · 44 · 58 px. Body is 17px / 1.6 in
a ~66ch measure. Tracking is tightened on display sizes only.

Fonts are loaded from Google Fonts in `index.html` with `display=swap` and
system fallbacks. To self-host (recommended for privacy), add the
`@fontsource` packages for the three families and import them in `main.jsx`,
then delete the `<link>` tags.

## Layout rules

- Content is stacked vertically, left-aligned, in a readable column. Every
  section follows the same order: numbered kicker, heading, sub-heading, then
  the content. Nothing is arranged in side-by-side columns of prose; lists of
  facts are rows with the label above or beside the value.
- The landing page and the signed-in dashboard share one set of sections
  (`EvidenceStory`), so a signed-in user sees the same evidence story plus
  their recent analyses.
- Related items sit 8-16px apart; sections are separated by 64-96px and a
  hairline rule.

## One accent, tokens only

All colours are tokens in `src/theme.css`. To change the accent, edit
`--accent`, `--accent-ink` and `--accent-wash` in both themes.

## Responsible and accessible by construction

- Claims are bounded in the copy: predictions are screens, not validation.
  Each report lists its limitations; the landing page says what is *not*
  claimed.
- Text contrast is at least 4.5:1 and control borders at least 3:1 in both
  themes (checked with a script in the repository history).
- Every interactive element has a visible focus ring and a 44px target.
- Skip link, landmarks, one `h1` per page, labelled controls, live regions for
  readouts.
- Motion is limited to short transitions and is disabled by
  `prefers-reduced-motion`.
- Charts are not colour-only: lanes are labelled, bars carry an outline, and
  every chart has a text alternative or a "same features as text" list.
- Charts can be magnified by buttons and keyboard (`+`, `-`, `0`, arrows).
  Scroll-wheel zoom needs Ctrl/⌘, so the page never traps scrolling.
- No third-party trackers. The only external request is the font stylesheet
  (see above to remove it).
