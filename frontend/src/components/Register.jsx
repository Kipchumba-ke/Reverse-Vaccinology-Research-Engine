import { useState } from 'react'
import { register } from '../services/authService'

function Register({ onRegister, onLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(event) {
    event.preventDefault()

    try {
      await register(email, password)
      onRegister()
      setSuccess(true)
      setError(null)
    } catch (err) {
      setError(err.message)
      setSuccess(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <label htmlFor="register-email">Email</label>
      <input
        id="register-email"
        type="email"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
      />

      <label htmlFor="register-password">Password</label>
      <input
        id="register-password"
        type="password"
        value={password}
        onChange={(event) => setPassword(event.target.value)}
      />

      <button type="submit">Register</button>
      <button type="button" onClick={onLogin}>Already have an account? Login</button>
      {success && <p>Registration successful!</p>}
      {error && <p>{error}</p>}
    </form>
  )
}

export default Register