import requests


def fetch_protein_annotation(accession: str) -> dict:
    if not accession:
        raise ValueError("Accession is required")

    try:
        response = requests.get(
            f"https://rest.uniprot.org/uniprotkb/{accession}.json"
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError("UniProt request failed") from exc

    data = response.json()

    protein_description = data.get("proteinDescription", {})
    recommended_name = protein_description.get("recommendedName", {})
    full_name = recommended_name.get("fullName", {})
    protein_name = full_name.get("value")

    return {
        "accession": data["primaryAccession"],
        "protein_name": protein_name,
    }
