
export async function getAnalysisHistory(token) {
  const response = await fetch('/api/analyses', {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  const data = await response.json()

  if (response.status === 401) {
    localStorage.removeItem('token')
    throw new Error('Your session has expired. Please log in again.')
  }

  if (!response.ok) {
    throw new Error(data.error || 'Unable to load analysis history.')
  }

  return data.analyses
}
