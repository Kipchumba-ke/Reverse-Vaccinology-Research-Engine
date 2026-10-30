"""IEDB Analysis Resource client: MHC-I and MHC-II binding, B-cell epitopes.

Uses the public REST service documented at
https://tools.iedb.org/main/tools-api/ . Off by default, because enabling it
sends the protein sequence to a third-party server:

    IEDB_ENABLED=1
    IEDB_API_BASE=https://tools-cluster-interface.iedb.org/tools_api
    IEDB_MHCI_ALLELES=HLA-A*01:01,HLA-A*02:01,...
    IEDB_MHCII_ALLELES=HLA-DRB1*01:01,...
    IEDB_MHCI_LENGTH=9
    IEDB_MHCII_LENGTH=15
    IEDB_MHCI_RANK_CUTOFF=1
    IEDB_MHCII_RANK_CUTOFF=10
    IEDB_MAX_SEQUENCE_LENGTH=1500
    IEDB_TIMEOUT_SECONDS=120

Endpoints, request parameters and method names (``recommended``,
``Bepipred-2.0``) were checked against the IEDB page. The page does not
document the response columns, so the parsers read the header row and match
columns by name, and fail with a clear message when a needed column is
missing. They have only been tested on hand-written samples, not on live
IEDB responses; run one real protein through the service before relying on
it.

Output is a prediction, not evidence that a peptide is presented or
recognised. A lower percentile rank means stronger predicted binding. The
rank cut-offs are provisional screening conventions, configurable above.
"""

import os

import requests

DEFAULT_BASE = "https://tools-cluster-interface.iedb.org/tools_api"

# Common HLA alleles, not a population-coverage-optimised panel.
DEFAULT_MHCI_ALLELES = (
    "HLA-A*01:01,HLA-A*02:01,HLA-A*03:01,HLA-A*24:02,"
    "HLA-B*07:02,HLA-B*08:01,HLA-B*35:01,HLA-B*44:02"
)
DEFAULT_MHCII_ALLELES = (
    "HLA-DRB1*01:01,HLA-DRB1*03:01,HLA-DRB1*04:01,HLA-DRB1*07:01,"
    "HLA-DRB1*11:01,HLA-DRB1*13:02,HLA-DRB1*15:01"
)

BCELL_METHOD = "Bepipred-2.0"
BCELL_SCORE_CUTOFF = 0.5
BCELL_MIN_REGION = 5

_RANK_COLUMNS = ("percentile_rank", "rank")


def is_iedb_enabled() -> bool:
    return os.environ.get("IEDB_ENABLED", "").strip().lower() in {
        "1", "true", "yes", "on",
    }


def _base() -> str:
    return os.environ.get("IEDB_API_BASE", DEFAULT_BASE).rstrip("/")


def _number(name: str, default: float) -> float:
    raw = os.environ.get(name)

    if raw is None or not raw.strip():
        return default

    try:
        value = float(raw)
    except ValueError as error:
        raise RuntimeError(f"{name} must be a number.") from error

    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero.")

    return value


def _alleles(name: str, default: str) -> list[str]:
    raw = os.environ.get(name) or default
    alleles = [item.strip() for item in raw.split(",") if item.strip()]

    if not alleles:
        raise RuntimeError(f"{name} must list at least one allele.")

    return alleles


def _post(tool: str, form: dict) -> str:
    timeout = _number("IEDB_TIMEOUT_SECONDS", 120)

    try:
        response = requests.post(
            f"{_base()}/{tool}/", data=form, timeout=timeout
        )
        response.raise_for_status()
    except requests.RequestException as error:
        raise RuntimeError(f"IEDB request failed: {error}") from error

    return response.text


def parse_binding_table(text: str) -> list[dict]:
    """Parse an MHC-I or MHC-II response into rows.

    The header row is the first line that mentions a peptide column.
    Columns are matched by name, so extra or reordered columns are fine.
    """
    lines = [line for line in text.splitlines() if line.strip()]
    header_index = next(
        (i for i, line in enumerate(lines) if "peptide" in line.lower()),
        None,
    )

    if header_index is None:
        raise ValueError(
            "IEDB response has no peptide column; first line was: "
            + (lines[0][:120] if lines else "(empty)")
        )

    header = [name.strip().lower() for name in lines[header_index].split("\t")]

    def find(*names):
        for name in names:
            if name in header:
                return header.index(name)
        return None

    peptide_col = find("peptide")
    rank_col = find(*_RANK_COLUMNS)

    if rank_col is None:
        rank_col = next(
            (i for i, name in enumerate(header) if "rank" in name), None
        )

    if peptide_col is None or rank_col is None:
        raise ValueError(
            "IEDB response is missing a percentile rank column; columns "
            "were: " + ", ".join(header)
        )

    allele_col = find("allele")
    start_col = find("start")
    end_col = find("end")
    core_col = find("core", "core_peptide")
    score_col = find("score", "ic50")

    rows = []

    for line in lines[header_index + 1:]:
        fields = line.split("\t")

        if len(fields) <= max(peptide_col, rank_col):
            continue

        try:
            rank = float(fields[rank_col])
            start = int(fields[start_col]) if start_col is not None else None
            end = int(fields[end_col]) if end_col is not None else None
            score = (
                float(fields[score_col])
                if score_col is not None and fields[score_col].strip()
                else None
            )
        except ValueError:
            continue

        peptide = fields[peptide_col].strip()
        rows.append({
            "allele": fields[allele_col].strip() if allele_col is not None
            else None,
            "peptide": peptide,
            "start": start,
            "end": end if end is not None else (
                start + len(peptide) - 1 if start is not None else None
            ),
            "core": fields[core_col].strip() if core_col is not None
            else None,
            "score": score,
            "percentile_rank": rank,
        })

    return rows


def collect_binders(rows: list[dict], cutoff: float) -> list[dict]:
    """Group rows at or below the rank cut-off by peptide position."""
    grouped: dict[tuple, dict] = {}

    for row in rows:
        if row["percentile_rank"] > cutoff or row["start"] is None:
            continue

        key = (row["start"], row["end"], row["peptide"])
        entry = grouped.setdefault(key, {
            "peptide": row["peptide"],
            "start": row["start"],
            "end": row["end"],
            "alleles": [],
        })
        entry["alleles"].append({
            "allele": row["allele"],
            "percentile_rank": row["percentile_rank"],
            "score": row["score"],
        })

    binders = list(grouped.values())

    for binder in binders:
        binder["alleles"].sort(key=lambda item: item["percentile_rank"])
        binder["allele_count"] = len(binder["alleles"])
        binder["best_percentile_rank"] = binder["alleles"][0][
            "percentile_rank"
        ]

    return sorted(
        binders,
        key=lambda b: (-b["allele_count"], b["best_percentile_rank"],
                       b["start"]),
    )


def _predict_binding(
    tool: str, sequence: str, alleles: list[str], length: str, cutoff: float
) -> dict:
    rows = []
    failed = {}

    # One request per allele keeps allele/length pairing unambiguous and
    # lets one failing allele leave the others intact.
    for allele in alleles:
        try:
            text = _post(tool, {
                "method": "recommended",
                "sequence_text": sequence,
                "allele": allele,
                "length": length,
            })
            rows.extend(parse_binding_table(text))
        except (RuntimeError, ValueError) as error:
            failed[allele] = str(error)

    binders = collect_binders(rows, cutoff)

    return {
        "method": "IEDB recommended",
        "alleles": alleles,
        "peptide_length": length,
        "rank_cutoff": cutoff,
        "predictions_returned": len(rows),
        "binders": binders,
        "alleles_failed": failed,
    }


def parse_bcell_table(text: str) -> list[dict]:
    """Parse a per-residue B-cell response (Position/Residue/Score)."""
    lines = [line for line in text.splitlines() if line.strip()]
    header_index = next(
        (i for i, line in enumerate(lines)
         if "position" in line.lower() and "score" in line.lower()),
        None,
    )

    if header_index is None:
        raise ValueError(
            "IEDB B-cell response has no Position/Score columns; first "
            "line was: " + (lines[0][:120] if lines else "(empty)")
        )

    header = [name.strip().lower() for name in lines[header_index].split("\t")]
    position_col = header.index("position")
    score_col = header.index("score")
    assignment_col = (
        header.index("assignment") if "assignment" in header else None
    )
    residue_col = header.index("residue") if "residue" in header else None

    residues = []

    for line in lines[header_index + 1:]:
        fields = line.split("\t")

        try:
            residues.append({
                "position": int(fields[position_col]),
                "residue": fields[residue_col].strip()
                if residue_col is not None else None,
                "score": float(fields[score_col]),
                "assigned": (
                    fields[assignment_col].strip().upper() == "E"
                    if assignment_col is not None else None
                ),
            })
        except (ValueError, IndexError):
            continue

    return residues


def bcell_regions(residues: list[dict], min_length: int = BCELL_MIN_REGION,
                  score_cutoff: float = BCELL_SCORE_CUTOFF) -> list[dict]:
    """Merge residues the tool called epitope (or above the score cut-off)."""
    def is_epitope(item):
        if item["assigned"] is not None:
            return item["assigned"]
        return item["score"] >= score_cutoff

    regions = []
    current = []

    for item in sorted(residues, key=lambda r: r["position"]) + [None]:
        if item is not None and is_epitope(item) and (
            not current or item["position"] == current[-1]["position"] + 1
        ):
            current.append(item)
            continue

        if len(current) >= min_length:
            regions.append({
                "start": current[0]["position"],
                "end": current[-1]["position"],
                "length": len(current),
                "mean_score": round(
                    sum(r["score"] for r in current) / len(current), 4
                ),
            })

        current = [item] if item is not None and is_epitope(item) else []

    return regions


def predict_bcell(sequence: str) -> dict:
    text = _post("bcell", {"method": BCELL_METHOD, "sequence_text": sequence})
    residues = parse_bcell_table(text)

    return {
        "method": BCELL_METHOD,
        "residues_scored": len(residues),
        "regions": bcell_regions(residues),
        "min_region_length": BCELL_MIN_REGION,
    }


def overlapping_region_summary(
    mhc_i: dict, mhc_ii: dict, bcell: dict
) -> list[dict]:
    """Regions where a B-cell epitope overlaps MHC-I or MHC-II binders."""
    def overlaps(a_start, a_end, b_start, b_end):
        return a_start <= b_end and a_end >= b_start

    summary = []

    for region in bcell.get("regions", []):
        i_hits = [b for b in mhc_i.get("binders", [])
                  if overlaps(region["start"], region["end"],
                              b["start"], b["end"])]
        ii_hits = [b for b in mhc_ii.get("binders", [])
                   if overlaps(region["start"], region["end"],
                               b["start"], b["end"])]

        if i_hits or ii_hits:
            summary.append({
                "start": region["start"],
                "end": region["end"],
                "mhc_i_binders": len(i_hits),
                "mhc_ii_binders": len(ii_hits),
            })

    return summary


def fetch_epitope_predictions(sequence: str) -> dict:
    """Run MHC-I, MHC-II and B-cell prediction; never raises."""
    try:
        max_length = int(_number("IEDB_MAX_SEQUENCE_LENGTH", 1500))
        mhci_alleles = _alleles("IEDB_MHCI_ALLELES", DEFAULT_MHCI_ALLELES)
        mhcii_alleles = _alleles("IEDB_MHCII_ALLELES", DEFAULT_MHCII_ALLELES)
        mhci_cutoff = _number("IEDB_MHCI_RANK_CUTOFF", 1.0)
        mhcii_cutoff = _number("IEDB_MHCII_RANK_CUTOFF", 10.0)
        mhci_length = str(int(_number("IEDB_MHCI_LENGTH", 9)))
        mhcii_length = str(int(_number("IEDB_MHCII_LENGTH", 15)))
    except RuntimeError as error:
        return {"status": "lookup_failed", "method": "IEDB",
                "message": str(error)}

    if len(sequence) > max_length:
        return {
            "status": "not_performed",
            "method": "IEDB",
            "message": (
                f"Sequence has {len(sequence)} residues, over the "
                f"{max_length}-residue limit set by IEDB_MAX_SEQUENCE_LENGTH."
            ),
        }

    mhc_i = _predict_binding(
        "mhci", sequence, mhci_alleles, mhci_length, mhci_cutoff
    )
    mhc_ii = _predict_binding(
        "mhcii", sequence, mhcii_alleles, mhcii_length, mhcii_cutoff
    )

    try:
        bcell = predict_bcell(sequence)
        bcell_error = None
    except (RuntimeError, ValueError) as error:
        bcell = {"method": BCELL_METHOD, "regions": []}
        bcell_error = str(error)

    nothing_returned = (
        not mhc_i["predictions_returned"]
        and not mhc_ii["predictions_returned"]
        and bcell_error is not None
    )

    if nothing_returned:
        return {
            "status": "lookup_failed",
            "method": "IEDB",
            "message": (
                bcell_error
                or "IEDB returned no predictions."
            ),
            "mhc_class_i": mhc_i,
            "mhc_class_ii": mhc_ii,
        }

    return {
        "status": "completed",
        "method": "IEDB Analysis Resource",
        "mhc_class_i": mhc_i,
        "mhc_class_ii": mhc_ii,
        "b_cell": bcell,
        "b_cell_error": bcell_error,
        "overlaps": overlapping_region_summary(mhc_i, mhc_ii, bcell),
        "notes": [
            "Predictions only. Lower percentile rank means stronger "
            "predicted binding; rank cut-offs are provisional.",
            "Alleles are a fixed panel and do not represent any "
            "population's HLA diversity.",
        ],
    }


def annotate_peptides_with_epitopes(
    peptides: list[dict], prediction: dict
) -> list[dict]:
    """Add predicted-epitope overlap fields to peptide windows."""
    if prediction.get("status") != "completed":
        return peptides

    def covering(binders, peptide):
        return {
            allele["allele"]
            for binder in binders
            if binder["start"] <= peptide["end"]
            and binder["end"] >= peptide["start"]
            for allele in binder["alleles"]
        }

    regions = prediction.get("b_cell", {}).get("regions", [])
    annotated = []

    for peptide in peptides:
        annotated.append({
            **peptide,
            "overlaps_b_cell_epitope": any(
                r["start"] <= peptide["end"] and r["end"] >= peptide["start"]
                for r in regions
            ),
            "mhc_i_binder_alleles": len(
                covering(prediction["mhc_class_i"]["binders"], peptide)
            ),
            "mhc_ii_binder_alleles": len(
                covering(prediction["mhc_class_ii"]["binders"], peptide)
            ),
        })

    return annotated
