export async function submitAnalysis(sequence, token) {
  const response = await fetch('/api/analyses', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      sequence,
    }),
  })

  return response.json()
}

export async function getAnalysisStatus(analysisId, token) {
  const response = await fetch(`/api/analyses/${analysisId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  return response.json()
}