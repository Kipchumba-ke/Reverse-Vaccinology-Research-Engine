import { handleUnauthorized } from './session'
import { apiUrl } from './apiBase'

export async function fetchStructure(accession, token) {
  const response = await fetch(apiUrl(`/api/structure/${encodeURIComponent(accession)}`), {
    headers: { Authorization: `Bearer ${token}` },
  })

  if (handleUnauthorized(response)) {
    throw new Error('Your session has expired. Please log in again.')
  }

  const data = await response.json().catch(() => ({}))

  if (!response.ok) {
    throw new Error(data.error || 'The structure could not be loaded.')
  }

  return data
}

// UniProt accession pattern, from the UniProt documentation.
const UNIPROT = /^([OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2})$/

export function isUniprotAccession(value) {
  return typeof value === 'string' && UNIPROT.test(value.trim().toUpperCase())
}
