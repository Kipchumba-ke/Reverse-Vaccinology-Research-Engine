import { SESSION_EXPIRED_MESSAGE, handleUnauthorized } from './session'
import { apiUrl, readJson } from './apiBase'


export async function getAnalysisHistory(token) {
  const response = await fetch(apiUrl('/api/analyses'), {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  const data = await readJson(response)

  if (handleUnauthorized(response)) {
    throw new Error(SESSION_EXPIRED_MESSAGE)
  }

  if (!response.ok) {
    throw new Error(data.error || 'Unable to load analysis history.')
  }

  return data.analyses
}


export async function deleteAnalysis(analysisId, token) {
  const response = await fetch(
    apiUrl(`/api/analyses/${encodeURIComponent(analysisId)}`),
    {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  )

  const data = await readJson(response)

  if (handleUnauthorized(response)) {
    throw new Error(SESSION_EXPIRED_MESSAGE)
  }

  if (!response.ok) {
    throw new Error(data.error || 'Unable to delete analysis.')
  }

  return data
}