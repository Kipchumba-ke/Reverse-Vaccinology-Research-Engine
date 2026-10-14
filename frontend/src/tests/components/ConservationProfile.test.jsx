import { describe, it, expect } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import ConservationProfile from '../../components/ConservationProfile'

describe('ConservationProfile', () => {
  it('renders an accessible conservation chart', () => {
    const alignment = ['MK-T', 'MKTT', 'MK-T']

    render(<ConservationProfile alignment={alignment} />)

    expect(
      screen.getByRole('img', {
        name: 'Per-position conservation profile',
      }),
    ).toBeInTheDocument()
  })

  it('reports 100% conservation for fully conserved positions', () => {
    const alignment = ['MK-T', 'MKTT', 'MK-T']

    render(<ConservationProfile alignment={alignment} />)

    const chart = screen.getByRole('img', {
      name: 'Per-position conservation profile',
    })

    const titles = chart.querySelectorAll('circle title')

    expect(titles).toHaveLength(4)

    titles.forEach((title) => {
      expect(title.textContent).toMatch(/100\.00%/)
    })
  })

  it('calculates mixed-column conservation correctly', () => {
    const alignment = ['A', 'A', 'G']

    render(<ConservationProfile alignment={alignment} />)

    expect(
        screen.getByRole('img').querySelector('circle title').textContent,
    ).toMatch(/Position\s+1\s*:\s*66\.67\s*%/)
  })

  it('excludes gaps from the conservation denominator', () => {
    const alignment = ['A-', 'A-', 'G-']

    render(<ConservationProfile alignment={alignment} />)

    expect(
        screen.getByRole('img').querySelector('circle title').textContent,
    ).toMatch(/Position\s+1\s*:\s*66\.67\s*%/)

    const chart = screen.getByRole('img', {
      name: 'Per-position conservation profile',
    })

    expect(
      within(chart).queryByTitle(/Position 2:/),
    ).not.toBeInTheDocument()
  })

  it('does not plot a point for a gap-only column', () => {
    const alignment = ['A-', 'A-', 'G-']

    render(<ConservationProfile alignment={alignment} />)

    const chart = screen.getByRole('img', {
      name: 'Per-position conservation profile',
    })

    expect(
      within(chart).queryByTitle(/Position 2:/),
    ).not.toBeInTheDocument()
  })

  it('shows a message when alignment data is empty', () => {
    render(<ConservationProfile alignment={[]} />)

    expect(
      screen.getByText(
        'No per-position conservation data is available.',
      ),
    ).toBeInTheDocument()
  })
})