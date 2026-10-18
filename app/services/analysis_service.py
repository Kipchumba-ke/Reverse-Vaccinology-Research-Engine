import os
import re

from app.analysis.blast import run_blast_analysis
from app.analysis.conservation import find_conserved_regions
from app.analysis.pipeline import analyze_protein
from app.analysis.workflow import (
    analyze_fasta_records as run_fasta_workflow,
)
from app.integrations.essentiality import fetch_essentiality_evidence
from app.integrations.ncbi import fetch_protein_record
from app.integrations.uniprot import fetch_protein_annotation
from app.models.analysis import Analysis
from app.reporting.report import generate_protein_report
from app.services.integration_service import (
    convert_uniprot_localizations,
    run_integrations,
)
from app.utils.validation import validate_protein_sequence
from app.models.host_similarity import HostSimilarityEvidence


def _is_ncbi_accession(accession: str) -> bool:
    """Recognize common NCBI/RefSeq protein accession formats."""
    return bool(
        re.search(r"\.\d+$", accession)
        or re.match(
            r"^(?:NP|XP|YP|WP|AP)_",
            accession,
            re.IGNORECASE,
        )
        or re.match(
            r"^[A-Z]{3}\d{5,}$",
            accession,
            re.IGNORECASE,
        )
    )


def fetch_localization_result(accession: str | None) -> dict:
    """Fetch localization annotations and retain lookup status."""
    if not accession or not accession.strip():
        return {
            "evidence": [],
            "annotation": None,
            "status": "not_attempted",
            "source": None,
            "message": (
                "No accession supplied; localization was not queried."
            ),
        }

    accession = accession.strip()
    is_ncbi = _is_ncbi_accession(accession)
    source = "NCBI Protein" if is_ncbi else "UniProt"

    try:
        annotation = (
            fetch_protein_record(accession)
            if is_ncbi
            else fetch_protein_annotation(accession)
        )
        evidence = convert_uniprot_localizations(annotation)

    except (RuntimeError, ValueError) as exc:
        return {
            "evidence": [],
            "annotation": None,
            "status": "lookup_failed",
            "source": source,
            "message": str(exc),
        }

    if not evidence:
        return {
            "evidence": [],
            "annotation": annotation,
            "status": "no_annotations",
            "source": source,
            "message": (
                f"{source} returned no usable localization annotations."
            ),
        }

    return {
        "evidence": evidence,
        "annotation": annotation,
        "status": "available",
        "source": source,
        "message": (
            f"Retrieved {len(evidence)} localization annotation(s) "
            f"from {source}."
        ),
    }


def fetch_localization_evidence(accession: str | None) -> list:
    """Backward-compatible evidence-only interface."""
    return fetch_localization_result(accession)["evidence"]


def _fetch_external_evidence(
    sequence: str,
    protein_id: str | None = None,
    accession: str | None = None,
    organism: str | None = None,
    blast_database: str | None = None,
    essentiality_data_path: str | None = None,
    run_host_search: bool = True,
) -> dict:
    """Retrieve external evidence without running protein analysis."""
    essentiality_data_path = (
        essentiality_data_path
        or os.environ.get("ESSENTIALITY_DATA_PATH")
    )

    try:
        essentiality = fetch_essentiality_evidence(
            dataset_path=essentiality_data_path,
            protein_id=protein_id,
            accession=accession,
            organism=organism,
        )
    except (RuntimeError, ValueError) as exc:
        essentiality = {
            "evidence": [],
            "status": "lookup_failed",
            "message": str(exc),
        }

    host_database = (
        blast_database or os.environ.get("HOST_BLAST_DATABASE")
    )

    if not run_host_search:
        host_status = {
            "status": "not_attempted",
            "message": (
                "Host-similarity evidence was supplied by another "
                "integration path or the search was skipped."
            ),
        }
        host_evidence = []
    elif not host_database:
        host_status = {
            "status": "not_configured",
            "message": "No host-proteome BLAST database configured.",
        }
        host_evidence = []
    else:
        try:
            host_evidence = run_blast_analysis(
                sequence,
                database=host_database,
                source="Host proteome BLAST",
                confidence="medium",
                description=(
                    "Sequence similarity search against the configured "
                    "host proteome. Hits require biological interpretation."
                ),
            )
            host_status = (
                {
                    "status": "hits_found",
                    "message": (
                        f"BLAST returned {len(host_evidence)} "
                        "host-proteome match(es). Review identity, "
                        "coverage, and E-value."
                    ),
                }
                if host_evidence
                else {
                    "status": "no_significant_hits",
                    "message": (
                        "No significant hits were returned under the "
                        "configured BLAST search settings. This does not "
                        "prove host similarity is absent."
                    ),
                }
            )
        except (RuntimeError, ValueError) as exc:
            host_evidence = []
            host_status = {
                "status": "lookup_failed",
                "message": str(exc),
            }

    return {
        "essentiality_evidence": essentiality.get("evidence", []),
        "essentiality": {
            "status": essentiality.get("status", "unknown"),
            "message": essentiality.get(
                "message",
                "Essentiality lookup status unavailable.",
            ),
        },
        "host_similarity_evidence": host_evidence,
        "host_similarity": host_status,
    }


def _attach_external_evidence(
    result,
    protein_id: str | None = None,
    accession: str | None = None,
    organism: str | None = None,
    blast_database: str | None = None,
    essentiality_data_path: str | None = None,
    run_host_search: bool = True,
) -> dict:
    """Attach available essentiality and host-similarity evidence."""
    essentiality_data_path = (
        essentiality_data_path
        or os.environ.get("ESSENTIALITY_DATA_PATH")
    )

    try:
        essentiality = fetch_essentiality_evidence(
            dataset_path=essentiality_data_path,
            protein_id=protein_id,
            accession=accession,
            organism=organism,
        )
    except (RuntimeError, ValueError) as exc:
        essentiality = {
            "evidence": [],
            "status": "lookup_failed",
            "message": str(exc),
        }

    result.essentiality_evidence.extend(
        essentiality.get("evidence", [])
    )

    host_database = (
        blast_database or os.environ.get("HOST_BLAST_DATABASE")
    )

    if not run_host_search:
        host_status = {
            "status": "not_attempted",
            "message": (
                "Host-similarity evidence was supplied by another "
                "integration path or the search was skipped."
            ),
        }
    elif not host_database:
        host_status = {
            "status": "not_configured",
            "message": (
                "No host-proteome BLAST database configured."
            ),
        }
    else:
        try:
            host_evidence = run_blast_analysis(
                result.sequence,
                database=host_database,
                source="Host proteome BLAST",
                confidence="medium",
                description=(
                    "Sequence similarity search against the configured "
                    "host proteome. Hits require biological interpretation."
                ),
            )
            result.host_similarity_evidence.extend(host_evidence)

            if host_evidence:
                host_status = {
                    "status": "hits_found",
                    "message": (
                        f"BLAST returned {len(host_evidence)} "
                        "host-proteome match(es). Review identity, "
                        "coverage, and E-value."
                    ),
                }
            else:
                host_status = {
                    "status": "no_significant_hits",
                    "message": (
                        "No significant hits were returned under the "
                        "configured BLAST search settings. This does not "
                        "prove host similarity is absent."
                    ),
                }

        except (RuntimeError, ValueError) as exc:
            host_status = {
                "status": "lookup_failed",
                "message": str(exc),
            }

    return {
        "essentiality": {
            "status": essentiality.get("status", "unknown"),
            "message": essentiality.get(
                "message",
                "Essentiality lookup status unavailable.",
            ),
        },
        "host_similarity": host_status,
    }


def _status_summary(localization: dict, external: dict) -> dict:
    """Build the report's evidence-status section."""
    return {
        "localization": {
            key: localization.get(key)
            for key in ("status", "source", "message")
        },
        **external,
    }


def analyze_sequence(
    sequence: str,
    protein_id: str | None = None,
    protein_name: str | None = None,
    organism: str | None = None,
    accession: str | None = None,
    blast_database: str | None = None,
    msa_sequences: list[str] | None = None,
):
    """Analyze one protein and attach available external evidence."""
    result = analyze_protein(
        sequence,
        protein_id=protein_id,
        protein_name=protein_name,
        organism=organism,
        accession=accession,
        aligned_sequences=msa_sequences,
    )

    localization = fetch_localization_result(accession)
    result.localization_evidence.extend(localization["evidence"])

    annotation = localization.get("annotation")
    if accession and not result.protein_name and annotation:
        result.protein_name = (
            annotation.get("protein_name") or result.protein_name
        )

    # When run_integrations is enabled, reuse its BLAST output rather
    # than performing a second host-similarity search.
    integrations = None
    run_combined_integrations = bool(
        accession and blast_database and msa_sequences
    )

    if run_combined_integrations:
        try:
            integrations = run_integrations(
                sequence=sequence,
                accession=accession,
                blast_database=blast_database,
                msa_sequences=msa_sequences,
            )


            blast_evidence = integrations.get("blast", [])

            if isinstance(blast_evidence, list):
                result.host_similarity_evidence.extend(
                    evidence
                    for evidence in blast_evidence
                    if isinstance(evidence, HostSimilarityEvidence)
                )
        except (RuntimeError, ValueError):
            # Keep the sequence analysis usable when optional
            # integrations fail; report status below.
            integrations = {
                "status": "lookup_failed",
                "message": "One or more external integrations failed.",
            }

    external_status = _attach_external_evidence(
        result,
        protein_id=protein_id,
        accession=accession,
        organism=organism,
        blast_database=blast_database,
        run_host_search=not run_combined_integrations,
    )

    if run_combined_integrations and integrations:
        if integrations.get("status") == "lookup_failed":
            external_status["host_similarity"] = {
                "status": "lookup_failed",
                "message": integrations["message"],
            }
        elif result.host_similarity_evidence:
            external_status["host_similarity"] = {
                "status": "hits_found",
                "message": (
                    "Host-similarity evidence was returned by the "
                    "configured integration."
                ),
            }

    report = generate_protein_report(result)
    report["evidence_status"] = _status_summary(
        localization,
        external_status,
    )

    if integrations is not None:
        report["integrations"] = integrations

    return report


def analyze_fasta_records(records: list[dict]):
    """Analyze FASTA records and attach evidence to each protein."""
    if len(records) == 1:
        record = records[0]
        return analyze_sequence(
            record["sequence"],
            protein_id=record.get("id"),
            protein_name=record.get("description"),
            organism=record.get("organism"),
            accession=record.get("accession"),
        )

    localization_evidence = {}
    essentiality_evidence = {}
    host_similarity_evidence = {}
    localization_status = {}
    external_status = {}

    for record in records:
        record_id = record["id"]
        accession = record.get("accession")
        organism = record.get("organism")

        localization = fetch_localization_result(accession)
        localization_evidence[record_id] = localization["evidence"]
        localization_status[record_id] = {
            key: localization.get(key)
            for key in ("status", "source", "message")
        }

        external = _fetch_external_evidence(
            sequence=record["sequence"],
            protein_id=record_id,
            accession=accession,
            organism=organism,
        )

        essentiality_evidence[record_id] = (
            external["essentiality_evidence"]
        )
        host_similarity_evidence[record_id] = (
            external["host_similarity_evidence"]
        )
        external_status[record_id] = {
            "essentiality": external["essentiality"],
            "host_similarity": external["host_similarity"],
        }


    workflow_result = run_fasta_workflow(
        records,
        localization_evidence=localization_evidence,
        essentiality_evidence=essentiality_evidence,
        host_similarity_evidence=host_similarity_evidence,
    )

    workflow_data = workflow_result.to_dict()
    protein_analyses = []

    for analysis in workflow_result.protein_analyses:
        protein_report = generate_protein_report(
            analysis,
            conservation_summary=workflow_result.conservation,
            conserved_regions=find_conserved_regions(
                analysis.conservation_columns
            ),
        )

        protein_id = analysis.protein_id
        protein_report["evidence_status"] = {
            "localization": localization_status.get(
                protein_id,
                {
                    "status": "not_attempted",
                    "source": None,
                    "message": "Localization lookup status unavailable.",
                },
            ),
            **external_status.get(protein_id, {}),
        }

        protein_analyses.append(
            {**analysis.to_dict(), **protein_report}
        )

    workflow_data["protein_analyses"] = protein_analyses
    return workflow_data


def persist_analysis(analysis, repository):
    """Persist an analysis through the supplied repository."""
    return repository.save(analysis)


def create_analysis(
    sequence: str,
    protein_id: str | None = None,
    protein_name: str | None = None,
    organism: str | None = None,
    accession: str | None = None,
):
    """Validate input and create an analysis model."""
    cleaned_sequence = validate_protein_sequence(sequence)

    return Analysis(
        protein_id=protein_id,
        protein_name=protein_name,
        organism=organism,
        accession=accession,
        sequence=cleaned_sequence,
    )


def run_analysis(
    sequence: str,
    repository,
    protein_id: str | None = None,
    protein_name: str | None = None,
    organism: str | None = None,
    accession: str | None = None,
    msa_sequences: list[str] | None = None,
):
    """Create, persist, and execute an analysis."""
    analysis = create_analysis(
        sequence,
        protein_id=protein_id,
        protein_name=protein_name,
        organism=organism,
        accession=accession,
    )

    persist_analysis(analysis, repository)

    return analyze_sequence(
        analysis.sequence,
        protein_id=analysis.protein_id,
        protein_name=analysis.protein_name,
        organism=analysis.organism,
        accession=analysis.accession,
        msa_sequences=msa_sequences,
    )
