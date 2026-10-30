"""Fetch a predicted protein structure from the AlphaFold Protein Structure
Database (https://alphafold.ebi.ac.uk).

This does not run structure prediction. It retrieves the model DeepMind and
EMBL-EBI already computed for a UniProt accession, so it only works for
proteins that have one. The model describes the UniProt reference sequence;
if the analysed sequence differs, residue numbers may not line up, so the
reference sequence is returned for the caller to compare.

Per-residue confidence (pLDDT, 0-100) is stored in the B-factor column of
the PDB file. Regions below 70 should not be read as reliable structure.
"""

import re
from functools import lru_cache
from urllib.parse import urlparse

import requests

API_URL = "https://alphafold.ebi.ac.uk/api/prediction"
ALLOWED_HOST = "alphafold.ebi.ac.uk"
MAX_PDB_BYTES = 8_000_000
TIMEOUT_SECONDS = 30

# UniProt accession format, from the UniProt documentation.
_ACCESSION = re.compile(
    r"^([OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9]([A-Z][A-Z0-9]{2}[0-9]){1,2})$"
)


class StructureNotFound(LookupError):
    """AlphaFold DB has no model for this accession."""


def normalise_accession(accession: str) -> str:
    candidate = (accession or "").strip().upper()

    if not _ACCESSION.match(candidate):
        raise ValueError(
            "AlphaFold models are looked up by UniProt accession "
            "(for example P0A911)."
        )

    return candidate


def plddt_from_pdb(pdb_text: str) -> list[dict]:
    """Per-residue pLDDT read from the B-factor of each residue's CA atom."""
    residues = []

    for line in pdb_text.splitlines():
        if not line.startswith("ATOM") or line[12:16].strip() != "CA":
            continue

        try:
            residues.append({
                "position": int(line[22:26]),
                "plddt": float(line[60:66]),
            })
        except ValueError:
            continue

    return residues


def confidence_band(plddt: float) -> str:
    if plddt > 90:
        return "very_high"
    if plddt > 70:
        return "high"
    if plddt > 50:
        return "low"
    return "very_low"


def _checked_url(url: str) -> str:
    parsed = urlparse(url or "")

    if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST:
        raise RuntimeError("AlphaFold returned an unexpected file location.")

    return url


@lru_cache(maxsize=32)
def fetch_structure(accession: str) -> dict:
    accession = normalise_accession(accession)

    try:
        response = requests.get(
            f"{API_URL}/{accession}", timeout=TIMEOUT_SECONDS
        )

        if response.status_code == 404:
            raise StructureNotFound(
                f"AlphaFold DB has no model for {accession}."
            )

        response.raise_for_status()
        entries = response.json()
    except StructureNotFound:
        raise
    except (requests.RequestException, ValueError) as error:
        raise RuntimeError(f"AlphaFold request failed: {error}") from error

    if not isinstance(entries, list) or not entries:
        raise StructureNotFound(f"AlphaFold DB has no model for {accession}.")

    entry = entries[0]

    try:
        pdb_url = _checked_url(entry["pdbUrl"])
        download = requests.get(pdb_url, timeout=TIMEOUT_SECONDS)
        download.raise_for_status()
    except KeyError as error:
        raise RuntimeError("AlphaFold response had no pdbUrl.") from error
    except requests.RequestException as error:
        raise RuntimeError(f"AlphaFold download failed: {error}") from error

    if len(download.content) > MAX_PDB_BYTES:
        raise RuntimeError("AlphaFold model file is too large to display.")

    pdb = download.text
    confidence = plddt_from_pdb(pdb)

    return {
        "accession": accession,
        "entry_id": entry.get("entryId"),
        "model_version": entry.get("latestVersion"),
        "model_created": entry.get("modelCreatedDate"),
        "organism": entry.get("organismScientificName"),
        "reference_sequence": entry.get("uniprotSequence"),
        "uniprot_start": entry.get("uniprotStart"),
        "uniprot_end": entry.get("uniprotEnd"),
        "pae_image_url": entry.get("paeImageUrl"),
        "mean_plddt": (
            round(sum(r["plddt"] for r in confidence) / len(confidence), 1)
            if confidence else None
        ),
        "confidence": confidence,
        "pdb": pdb,
        "source": "AlphaFold Protein Structure Database",
        "notes": [
            "Predicted structure, not an experimental one. Regions with "
            "pLDDT below 70 are low confidence.",
        ],
    }
