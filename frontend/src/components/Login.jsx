import { useState } from 'react'
import { login } from '../services/authService'

function Login({ onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(event) {
    event.preventDefault()

    try {
      await login(email, password)
      onLogin()
      setSuccess(true)
      setError(null)
    } catch (err) {
      setError(err.message)
      setSuccess(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="login-email">Email</label>
      <input
        id="login-email"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
      />

      <label htmlFor="login-password">Password</label>
      <input
        id="login-password"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
      />

      <button type="submit">Login</button>
      {success && <p>Login successful!</p>}
      {error && <p>{error}</p>}
    </form>
  )
}

export default Login