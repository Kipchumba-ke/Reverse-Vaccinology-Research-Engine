import { describe, it, expect } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import { EvidenceStory } from '../../components/EvidenceStory'

describe('EvidenceStory', () => {
  it('renders each section with a heading and a sub-heading, in order', () => {
    const { container } = render(<EvidenceStory primaryAction={<button>Go</button>} />)

    const sections = [...container.querySelectorAll('section.section')]
    expect(sections.map((s) => s.id)).toEqual([
      'problem',
      'method',
      'paths',
      'standards',
      'responsible',
    ])

    sections.forEach((section) => {
      const head = section.querySelector('.section-head')
      expect([...head.children].map((el) => el.tagName)).toEqual(['P', 'H2', 'P'])
    })
  })

  it('lists each method question with its source and stated limit', () => {
    render(<EvidenceStory primaryAction={null} />)

    const method = document.getElementById('method')
    expect(within(method).getAllByRole('heading', { level: 3 })).toHaveLength(5)
    expect(within(method).getAllByText('Stated limit')).toHaveLength(5)
  })

  it('gives each audience a path and places the primary action with researchers', () => {
    render(<EvidenceStory primaryAction={<button>Start here</button>} />)

    const researchers = screen.getByRole('heading', { name: 'Researchers' }).closest('article')
    expect(within(researchers).getByRole('button', { name: 'Start here' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Investors' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Commercial partners' })).toBeInTheDocument()
  })
})
