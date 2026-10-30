import { describe, it, expect } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import ZoomFigure from '../../components/ZoomFigure'

function setup() {
  render(
    <ZoomFigure label="Demo chart">
      <svg role="img" aria-label="demo svg" />
    </ZoomFigure>,
  )
  return {
    level: () => screen.getByText(/%$/),
    viewport: () => screen.getByRole('group', { name: /demo chart\./i }),
  }
}

describe('ZoomFigure', () => {
  it('starts at 100% with zoom-out and reset disabled', () => {
    const { level } = setup()

    expect(level()).toHaveTextContent('100%')
    expect(screen.getByRole('button', { name: /zoom out demo chart/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /reset zoom for demo chart/i })).toBeDisabled()
  })

  it('zooms in and resets with the buttons', () => {
    const { level } = setup()

    fireEvent.click(screen.getByRole('button', { name: /zoom in demo chart/i }))
    expect(level()).toHaveTextContent('150%')

    fireEvent.click(screen.getByRole('button', { name: /zoom in demo chart/i }))
    expect(level()).toHaveTextContent('225%')

    fireEvent.click(screen.getByRole('button', { name: /reset zoom for demo chart/i }))
    expect(level()).toHaveTextContent('100%')
  })

  it('supports keyboard zoom: plus, minus and zero', () => {
    const { level, viewport } = setup()

    fireEvent.keyDown(viewport(), { key: '+' })
    expect(level()).toHaveTextContent('150%')

    fireEvent.keyDown(viewport(), { key: '-' })
    expect(level()).toHaveTextContent('100%')

    fireEvent.keyDown(viewport(), { key: '+' })
    fireEvent.keyDown(viewport(), { key: '0' })
    expect(level()).toHaveTextContent('100%')
  })

  it('zooms with Ctrl + wheel but leaves a plain wheel alone', () => {
    const { level, viewport } = setup()

    fireEvent.wheel(viewport(), { deltaY: -100 })
    expect(level()).toHaveTextContent('100%')

    fireEvent.wheel(viewport(), { deltaY: -100, ctrlKey: true })
    expect(level()).toHaveTextContent('150%')
  })

  it('never zooms beyond 800%', () => {
    const { level } = setup()

    for (let i = 0; i < 12; i += 1) {
      fireEvent.click(screen.getByRole('button', { name: /zoom in demo chart/i }))
    }

    expect(level()).toHaveTextContent('800%')
  })
})
