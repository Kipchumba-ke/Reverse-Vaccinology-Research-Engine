import os
import re

from pathlib import Path

from app.analysis.blast import run_blast_analysis
from app.analysis.conservation import find_conserved_regions
from app.analysis.pipeline import analyze_protein
from app.analysis.workflow import (
    analyze_fasta_records as run_fasta_workflow,
)
from app.integrations.essentiality import fetch_essentiality_evidence
from app.integrations.epath_essentiality import (
    fetch_epath_essentiality_evidence,
)
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


def _resolve_host_reference(
    host_reference: str | None,
    blast_database: str | None = None,
) -> tuple[str | None, bool]:
    """Resolve the selected host reference to a BLAST database.

    Returns:
        (database_path, should_run_search)
    """
    if host_reference is None:
        # Preserve compatibility with existing callers.
        database = blast_database or os.environ.get("HOST_BLAST_DATABASE")
        return database, True

    reference = host_reference.strip().lower()

    if reference == "none":
        return None, False

    if reference not in {"human", "mouse", "pig"}:
        raise ValueError("host_reference must be human, mouse, pig, or none.")

    environment_variable = {
        "human": "HOST_BLAST_DATABASE_HUMAN",
        "mouse": "HOST_BLAST_DATABASE_MOUSE",
        "pig": "HOST_BLAST_DATABASE_PIG",
    }[reference]

    # Explicit configuration takes precedence over local defaults.
    database = os.environ.get(environment_variable)

    if database:
        return database, True

    # Fall back to the corresponding local reference database.
    project_root = Path(__file__).resolve().parents[2]
    local_databases = {
        "human": (project_root / "data" / "reference" / "human" / "human_proteome_db"),
        "mouse": (project_root / "data" / "reference" / "mouse" / "mouse_proteome_db"),
        "pig": (project_root / "data" / "reference" / "pig" / "pig_proteome_db"),
    }

    local_database = local_databases[reference]

    if Path(f"{local_database}.pin").is_file():
        return str(local_database), True

    # Keep the selected host reference, but allow the calling
    # workflow to handle the absence of a configured database.
    return None, True


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
            "message": ("No accession supplied; localization was not queried."),
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
            "message": (f"{source} returned no usable localization annotations."),
        }

    return {
        "evidence": evidence,
        "annotation": annotation,
        "status": "available",
        "source": source,
        "message": (
            f"Retrieved {len(evidence)} localization annotation(s) " f"from {source}."
        ),
    }


def fetch_localization_evidence(accession: str | None) -> list:
    """Backward-compatible evidence-only interface."""
    return fetch_localization_result(accession)["evidence"]


def _fetch_epath_evidence(
    organism: str | None,
    epath_gene_id: str | None = None,
    epath_ko_id: str | None = None,
) -> dict:
    """Fetch ePath evidence only when an explicit ePath identifier is supplied.

    Protein accessions and FASTA record IDs are deliberately not used as
    ePath identifiers because they are not guaranteed to map to ePath genes.
    """
    if not epath_gene_id and not epath_ko_id:
        return {
            "evidence": [],
            "status": "not_requested",
            "message": ("No explicit ePath gene or KO identifier was supplied."),
        }

    try:
        return fetch_epath_essentiality_evidence(
            organism=organism,
            gene_id=epath_gene_id,
            ko_id=epath_ko_id,
        )
    except (RuntimeError, ValueError) as exc:
        return {
            "evidence": [],
            "status": "lookup_failed",
            "message": str(exc),
        }


def _fetch_external_evidence(
    sequence: str,
    protein_id: str | None = None,
    accession: str | None = None,
    organism: str | None = None,
    blast_database: str | None = None,
    essentiality_data_path: str | None = None,
    run_host_search: bool = True,
    epath_gene_id: str | None = None,
    epath_ko_id: str | None = None,
    host_reference: str | None = None,
) -> dict:
    """Retrieve external evidence without running protein analysis."""
    essentiality_data_path = essentiality_data_path or os.environ.get(
        "ESSENTIALITY_DATA_PATH"
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

    epath_essentiality = _fetch_epath_evidence(
        organism=organism,
        epath_gene_id=epath_gene_id,
        epath_ko_id=epath_ko_id,
    )

    host_database, should_run_host_search = _resolve_host_reference(
        host_reference=host_reference,
        blast_database=blast_database,
    )

    should_run_host_search = should_run_host_search and run_host_search

    if not should_run_host_search:
        host_status = {
            "status": "not_attempted",
            "host_reference": host_reference,
            "message": (
                "Host-similarity search was explicitly disabled."
                if host_reference is not None
                and host_reference.strip().lower() == "none"
                else (
                    "Host-similarity evidence was supplied by another "
                    "integration path or the search was skipped."
                )
            ),
        }
        host_evidence = []
    elif not host_database:
        host_status = {
            "status": "not_configured",
            "host_reference": host_reference,
            "message": (
                f"No BLAST database is configured for host reference "
                f"'{host_reference}'."
                if host_reference is not None
                else "No host-proteome BLAST database configured."
            ),
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
                    "host_reference": host_reference,
                }
                if host_evidence
                else {
                    "status": "no_significant_hits",
                    "message": (
                        "No significant hits were returned under the "
                        "configured BLAST search settings. This does not "
                        "prove host similarity is absent."
                    ),
                    "host_reference": host_reference,
                }
            )
        except (RuntimeError, ValueError) as exc:
            host_evidence = []
            host_status = {
                "status": "lookup_failed",
                "message": str(exc),
                "host_reference": host_reference,
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
        "epath_essentiality_evidence": epath_essentiality.get("evidence", []),
        "epath_essentiality": {
            "status": epath_essentiality.get("status", "unknown"),
            "message": epath_essentiality.get(
                "message",
                "ePath essentiality lookup status unavailable.",
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
    epath_gene_id: str | None = None,
    epath_ko_id: str | None = None,
    host_reference: str | None = None,
) -> dict:
    """Attach available essentiality and host-similarity evidence."""
    essentiality_data_path = essentiality_data_path or os.environ.get(
        "ESSENTIALITY_DATA_PATH"
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

    epath_essentiality = _fetch_epath_evidence(
        organism=organism,
        epath_gene_id=epath_gene_id,
        epath_ko_id=epath_ko_id,
    )

    result.essentiality_evidence.extend(essentiality.get("evidence", []))
    result.essentiality_evidence.extend(epath_essentiality.get("evidence", []))

    host_database, should_run_host_search = _resolve_host_reference(
        host_reference=host_reference,
        blast_database=blast_database,
    )

    should_run_host_search = should_run_host_search and run_host_search

    if not should_run_host_search:
        host_status = {
            "status": "not_attempted",
            "host_reference": host_reference,
            "message": (
                "Host-similarity search was explicitly disabled."
                if host_reference is not None
                and host_reference.strip().lower() == "none"
                else (
                    "Host-similarity evidence was supplied by another "
                    "integration path or the search was skipped."
                )
            ),
        }
        host_evidence = []
    elif not host_database:
        host_status = {
            "status": "not_configured",
            "host_reference": host_reference,
            "message": (
                f"No BLAST database is configured for host reference "
                f"'{host_reference}'."
                if host_reference is not None
                else "No host-proteome BLAST database configured."
            ),
        }
        host_evidence = []
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
                    "host_reference": host_reference,
                }
            else:
                host_status = {
                    "status": "no_significant_hits",
                    "message": (
                        "No significant hits were returned under the "
                        "configured BLAST search settings. This does not "
                        "prove host similarity is absent."
                    ),
                    "host_reference": host_reference,
                }

        except (RuntimeError, ValueError) as exc:
            host_status = {
                "status": "lookup_failed",
                "message": str(exc),
                "host_reference": host_reference,
            }

    return {
        "essentiality": {
            "status": essentiality.get("status", "unknown"),
            "message": essentiality.get(
                "message",
                "Essentiality lookup status unavailable.",
            ),
        },
        "epath_essentiality": {
            "status": epath_essentiality.get("status", "unknown"),
            "message": epath_essentiality.get(
                "message",
                "ePath essentiality lookup status unavailable.",
            ),
        },
        "host_similarity": host_status,
    }


def _status_summary(localization: dict, external: dict) -> dict:
    """Build the report's evidence-status section."""
    return {
        "localization": {
            key: localization.get(key) for key in ("status", "source", "message")
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
    epath_gene_id: str | None = None,
    epath_ko_id: str | None = None,
    host_reference: str | None = None,
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
        result.protein_name = annotation.get("protein_name") or result.protein_name

    # When run_integrations is enabled, reuse its BLAST output rather
    # than performing a second host-similarity search.
    integrations = None

    host_database, should_run_host_search = _resolve_host_reference(
        host_reference=host_reference,
        blast_database=blast_database,
    )

    host_search_disabled = not should_run_host_search

    run_combined_integrations = bool(
        not host_search_disabled and host_database and accession and msa_sequences
    )

    if run_combined_integrations:
        try:
            integrations = run_integrations(
                sequence=sequence,
                accession=accession,
                blast_database=host_database,
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
        epath_gene_id=epath_gene_id,
        epath_ko_id=epath_ko_id,
        host_reference=host_reference,
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


def analyze_fasta_records(
    records: list[dict],
    epath_gene_id: str | None = None,
    epath_ko_id: str | None = None,
    organism: str | None = None,
    host_reference: str | None = None,
):
    """Analyze FASTA records and attach evidence to each protein."""
    if len(records) == 1:
        record = records[0]
        return analyze_sequence(
            record["sequence"],
            protein_id=record.get("id"),
            protein_name=record.get("description"),
            organism=organism or record.get("organism"),
            accession=record.get("accession"),
            epath_gene_id=epath_gene_id,
            epath_ko_id=epath_ko_id,
            host_reference=host_reference,
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
            key: localization.get(key) for key in ("status", "source", "message")
        }

        external = _fetch_external_evidence(
            sequence=record["sequence"],
            protein_id=record_id,
            accession=accession,
            organism=organism,
            epath_gene_id=epath_gene_id,
            epath_ko_id=epath_ko_id,
            host_reference=host_reference,
        )

        essentiality_evidence[record_id] = external["essentiality_evidence"]
        host_similarity_evidence[record_id] = external["host_similarity_evidence"]
        external_status[record_id] = {
            "essentiality": external["essentiality"],
            "epath_essentiality": external.get(
                "epath_essentiality",
                {
                    "status": "unknown",
                    "message": "ePath essentiality lookup status unavailable.",
                },
            ),
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
            conserved_regions=find_conserved_regions(analysis.conservation_columns),
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

        protein_analyses.append({**analysis.to_dict(), **protein_report})

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
    epath_gene_id: str | None = None,
    epath_ko_id: str | None = None,
    host_reference: str | None = None,
):
    """Validate input and create an analysis model."""
    cleaned_sequence = validate_protein_sequence(sequence)

    return Analysis(
        protein_id=protein_id,
        protein_name=protein_name,
        organism=organism,
        accession=accession,
        sequence=cleaned_sequence,
        epath_gene_id=epath_gene_id,
        epath_ko_id=epath_ko_id,
        host_reference=host_reference,
    )


def run_analysis(
    sequence: str,
    repository,
    protein_id: str | None = None,
    protein_name: str | None = None,
    organism: str | None = None,
    accession: str | None = None,
    msa_sequences: list[str] | None = None,
    epath_gene_id: str | None = None,
    epath_ko_id: str | None = None,
    host_reference: str | None = None,
):
    """Create, persist, and execute an analysis."""
    analysis = create_analysis(
        sequence,
        protein_id=protein_id,
        protein_name=protein_name,
        organism=organism,
        accession=accession,
        epath_gene_id=epath_gene_id,
        epath_ko_id=epath_ko_id,
        host_reference=host_reference,
    )

    persist_analysis(analysis, repository)

    return analyze_sequence(
        analysis.sequence,
        protein_id=analysis.protein_id,
        protein_name=analysis.protein_name,
        organism=analysis.organism,
        accession=analysis.accession,
        msa_sequences=msa_sequences,
        epath_gene_id=analysis.epath_gene_id,
        epath_ko_id=analysis.epath_ko_id,
        host_reference=analysis.host_reference,
    )
