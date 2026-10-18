
import requests


UNIPROT_BASE_URL = "https://rest.uniprot.org/uniprotkb"


def fetch_protein_annotation(accession: str) -> dict:
    if not accession:
        raise ValueError("Accession is required")

    try:
        response = requests.get(
            f"{UNIPROT_BASE_URL}/{accession}.json",
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise RuntimeError("UniProt request failed") from exc

    if not isinstance(data, dict):
        raise RuntimeError("UniProt returned an invalid response")
    protein_description = data.get("proteinDescription", {})
    recommended_name = protein_description.get("recommendedName", {})
    full_name = recommended_name.get("fullName", {})
    protein_name = full_name.get("value")

    localization_annotations = []

    for comment in data.get("comments", []):
        if comment.get("commentType") != "SUBCELLULAR LOCATION":
            continue

        for subcellular_location in comment.get(
            "subcellularLocations", []
        ):
            location = subcellular_location.get("location", {})
            location_name = location.get("value")

            if not location_name:
                continue

            evidence_codes = [
                evidence.get("evidenceCode")
                for evidence in location.get("evidences", [])
                if evidence.get("evidenceCode")
            ]

            localization_annotations.append({
                "location": location_name,
                "source": "UniProt",
                "evidence_codes": evidence_codes,
            })

    return {
        "accession": data["primaryAccession"],
        "protein_name": protein_name,
        "localization_annotations": localization_annotations,
    }
