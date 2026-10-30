import { handleUnauthorized } from './session'

export async function submitAnalysis(sequence, token, metadata = {}) {
  const response = await fetch('/api/analyses', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      sequence,
      organism: metadata.organism || null,
      epath_gene_id: metadata.epath_gene_id || null,
      epath_ko_id: metadata.epath_ko_id || null,
      host_reference: metadata.host_reference ?? 'none',
    }),
  })

  handleUnauthorized(response)

  return response.json()
}

export async function submitFastaAnalysis(fastaContent, token, metadata = {}) {
  const response = await fetch('/api/analyses', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      fasta_content: fastaContent,
      organism: metadata.organism || null,
      epath_gene_id: metadata.epath_gene_id || null,
      epath_ko_id: metadata.epath_ko_id || null,
      host_reference: metadata.host_reference ?? 'none',
    }),
  })

  handleUnauthorized(response)

  return response.json()
}

export async function getAnalysisStatus(analysisId, token) {
  const response = await fetch(`/api/analyses/${analysisId}`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })

  handleUnauthorized(response)

  return response.json()
}


export async function downloadAnalysisReport(analysisId, token) {
  const response = await fetch(
    `/api/analyses/${analysisId}/report.pdf`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  )

  handleUnauthorized(response)

  if (!response.ok) {
    let message = 'Unable to download the analysis report.'

    try {
      const data = await response.json()
      if (data.error) message = data.error
    } catch {}

    throw new Error(message)
  }

  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = `analysis-${analysisId}.pdf`
  document.body.appendChild(link)
  link.click()
  link.remove()

  URL.revokeObjectURL(url)
}
