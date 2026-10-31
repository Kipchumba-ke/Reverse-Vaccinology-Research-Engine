import { afterEach, describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import DemoNotice from '../../components/DemoNotice'

afterEach(() => {
  vi.unstubAllEnvs()
})

describe('DemoNotice', () => {
  it('renders nothing unless the site is built as a demo', () => {
    const { container } = render(<DemoNotice />)

    expect(container).toBeEmptyDOMElement()
  })

  it('explains that this is an interface-only demo and links the code', () => {
    vi.stubEnv('VITE_DEMO_NOTICE', 'true')

    render(<DemoNotice />)

    expect(screen.getByText(/portfolio demo: interface only/i)).toBeInTheDocument()
    expect(screen.getByText(/signing in, registering/i)).toBeInTheDocument()

    const code = screen.getByRole('link', { name: /read the code on github/i })
    expect(code).toHaveAttribute(
      'href',
      'https://github.com/Kipchumba-ke/reverse-vaccinology-research-engine',
    )
    expect(code).toHaveAttribute('rel', 'noopener noreferrer')
  })

  it('links the demo video only when its address is an https URL', () => {
    vi.stubEnv('VITE_DEMO_NOTICE', 'true')

    const { unmount } = render(<DemoNotice />)
    expect(screen.queryByRole('link', { name: /watch the 2–3 minute demo/i })).toBeNull()
    unmount()

    vi.stubEnv('VITE_DEMO_VIDEO_URL', 'javascript:alert(1)')
    const second = render(<DemoNotice />)
    expect(screen.queryByRole('link', { name: /watch the 2–3 minute demo/i })).toBeNull()
    second.unmount()

    vi.stubEnv('VITE_DEMO_VIDEO_URL', 'https://example.com/demo')
    render(<DemoNotice />)
    expect(
      screen.getByRole('link', { name: /watch the 2–3 minute demo/i }),
    ).toHaveAttribute('href', 'https://example.com/demo')
  })
})
