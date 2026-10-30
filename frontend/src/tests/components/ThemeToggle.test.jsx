import { describe, it, expect, beforeEach } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import ThemeToggle from '../../components/ThemeToggle'
import { DEFAULT_THEME, THEME_STORAGE_KEY } from '../../theme'

describe('ThemeToggle', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  it('defaults to the dark theme', () => {
    render(<ThemeToggle />)

    expect(DEFAULT_THEME).toBe('dark')
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
    expect(
      screen.getByRole('button', { name: /switch to light theme/i }),
    ).toBeInTheDocument()
  })

  it('switches to light, remembers the choice, and switches back', () => {
    render(<ThemeToggle />)

    fireEvent.click(screen.getByRole('button', { name: /switch to light theme/i }))

    expect(document.documentElement).toHaveAttribute('data-theme', 'light')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('light')

    fireEvent.click(screen.getByRole('button', { name: /switch to dark theme/i }))

    expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('dark')
  })

  it('restores a saved light theme on the next visit', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'light')

    render(<ThemeToggle />)

    expect(document.documentElement).toHaveAttribute('data-theme', 'light')
    expect(
      screen.getByRole('button', { name: /switch to dark theme/i }),
    ).toBeInTheDocument()
  })

  it('ignores an unrecognised saved value', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'purple')

    render(<ThemeToggle />)

    expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
  })
})
