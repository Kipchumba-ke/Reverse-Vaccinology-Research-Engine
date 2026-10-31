import { useState } from 'react'
import { login } from '../services/authService'
import ThemeToggle from './ThemeToggle'
import DemoNotice from './DemoNotice'
import './Auth.css'

function Login({ onLogin, onRegister }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(event) {
    event.preventDefault()

    try {
      await login(email, password)
      onLogin?.()
      setSuccess(true)
      setError(null)
    } catch (err) {
      setError(err.message)
      setSuccess(false)
    }
  }

  return (
    <main className="auth-page" id="main">
      <a className="skip-link" href="#auth-form-region">Skip to form</a>
      <aside className="auth-aside">
        <a className="wordmark" href="/">
          ReverseVax
          <span>evidence ledger</span>
        </a>
        <p className="auth-aside-claim">
          Every claim in a report carries its source and its limits.
        </p>
        <p className="auth-aside-note">
          Computational screens to decide which proteins go to the bench
          first. Not experimental validation.
        </p>
        <DemoNotice />
      </aside>
      <section id="auth-form-region" className="auth-card" aria-labelledby="login-heading">

        <h1 className="auth-heading" id="login-heading">
          Welcome back
        </h1>

        <p className="auth-description">
          Sign in to continue your protein analysis and research.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="auth-label" htmlFor="login-email">
            Email address
          </label>
          <input
            className="auth-input"
            id="login-email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />

          <label className="auth-label" htmlFor="login-password">
            Password
          </label>
          <input
            className="auth-input"
            id="login-password"
            type="password"
            autoComplete="current-password"
            placeholder="Enter your password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />

          <button className="auth-primary-button" type="submit">
            Login
          </button>

          {success && (
            <p className="auth-message auth-message-success" role="status">
              Login successful!
            </p>
          )}

          {error && (
            <p className="auth-message auth-message-error" role="alert">
              {error}
            </p>
          )}

          <p className="auth-switch">
            Don't have an account?{' '}
            <button
              className="auth-switch-button"
              type="button"
              onClick={onRegister}
            >
              Register
            </button>
          </p>

        </form>
        <div className="auth-theme"><ThemeToggle /></div>
      </section>
    </main>
  )
}

export default Login
