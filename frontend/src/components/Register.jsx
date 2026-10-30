
import { useState } from 'react'
import { register } from '../services/authService'
import ThemeToggle from './ThemeToggle'
import './Auth.css'

function Register({ onRegister, onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(event) {
    event.preventDefault()

    try {
      await register(email, password)
      setSuccess(true)
      setError(null)
      onRegister?.()
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
      </aside>
      <section id="auth-form-region" className="auth-card" aria-labelledby="register-heading">

        <h1 className="auth-heading" id="register-heading">
          Create your account
        </h1>

        <p className="auth-description">
          Get started with protein analysis and explainable research insights.
        </p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="auth-label" htmlFor="register-email">
            Email address
          </label>
          <input
            className="auth-input"
            id="register-email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />

          <label className="auth-label" htmlFor="register-password">
            Password
          </label>
          <input
            className="auth-input"
            id="register-password"
            type="password"
            autoComplete="new-password"
            placeholder="Create a password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />

          <button className="auth-primary-button" type="submit">
            Register
          </button>

          {success && (
            <p className="auth-message auth-message-success" role="status">
              Registration successful!
            </p>
          )}

          {error && (
            <p className="auth-message auth-message-error" role="alert">
              {error}
            </p>
          )}

          <p className="auth-switch">
            <button
              className="auth-switch-button"
              type="button"
              onClick={onLogin}
              aria-label="Already have an account? Login"
            >
              Already have an account? Login
            </button>
          </p>
        </form>
        <div className="auth-theme"><ThemeToggle /></div>
      </section>
    </main>
  )
}

export default Register
