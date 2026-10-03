export async function submitAnalysis(sequence) {
  const response = await fetch('/api/analyses', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      sequence,
    }),
  })

  return response.json()
}

export async function getAnalysisStatus(analysisId) {
  const response = await fetch(`/api/analyses/${analysisId}`)

  return response.json()
}