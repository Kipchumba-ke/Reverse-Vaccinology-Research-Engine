export async function submitAnalysis(sequence, token) {
  const response = await fetch('http://127.0.0.1:5000/api/analyses', {
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
  const response = await fetch(`http://127.0.0.1:5000/api/analyses/${analysisId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  return response.json()
}