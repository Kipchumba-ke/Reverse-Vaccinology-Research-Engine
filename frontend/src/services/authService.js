import { apiUrl, readJson } from './apiBase'

export async function login(email, password) {
  const response = await fetch(apiUrl('/api/login'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email,
      password,
    }),
  })

  const result = await readJson(response)

  if (!response.ok) {
    throw new Error(result.error || 'Login failed')
  }

  if(result.token){
    localStorage.setItem('token', result.token)
  }

  return result
}
export async function register(email, password) {
  const response = await fetch(apiUrl('/api/register'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email,
      password,
    }),
  })

  return readJson(response)
}
