from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import HRFlowable


# The palette is the light ("warm paper") theme of the web app, see
# frontend/src/theme.css and frontend/DESIGN.md. The PDF is always light so
# that it prints and reads the same everywhere.
PAPER = colors.HexColor("#FBF9F4")
INK = colors.HexColor("#1F1E1D")
INK_SOFT = colors.HexColor("#504D46")
INK_FAINT = colors.HexColor("#6B675E")
RULE = colors.HexColor("#D9D4C5")
RULE_STRONG = colors.HexColor("#8B877B")
WASH = colors.HexColor("#EBE7DB")
ACCENT = colors.HexColor("#A93D19")
OK = colors.HexColor("#2F6B43")
WARN = colors.HexColor("#7A5A0E")
BAD = colors.HexColor("#A4261C")

ACCENT_HEX = "#A93D19"

# Built-in PDF fonts stand in for the web fonts: Times for text (Source
# Serif), Helvetica for the interface (IBM Plex Sans) and Courier for data
# (IBM Plex Mono). They need no files and are always available.
SERIF = "Times-Roman"
SERIF_BOLD = "Times-Bold"
SERIF_ITALIC = "Times-Italic"
SANS = "Helvetica"
SANS_BOLD = "Helvetica-Bold"
MONO = "Courier"

PAGE_MARGIN = 17 * mm
CONTENT_WIDTH = A4[0] - 2 * PAGE_MARGIN

# External predictors, in the order the web report lists them:
# (key in sequence_predictions, key in prediction_status, name, purpose).
PREDICTORS = [
    ("signalp", "signalp", "SignalP 6.0", "Signal peptide and cleavage site."),
    (
        "deeptmhmm", "deeptmhmm", "DeepTMHMM",
        "Transmembrane topology and protein class.",
    ),
    ("psortb", "psortb", "PSORTb 3.0", "Subcellular localization in bacteria."),
    (
        "epitopes", "iedb", "IEDB",
        "MHC binding and B-cell epitope predictions.",
    ),
]

STATE_LABELS = {
    "completed": ("Completed", OK),
    "not_configured": ("Not set up", WARN),
    "lookup_failed": ("Failed", BAD),
    "not_performed": ("Not performed", INK_SOFT),
    "not_enabled": ("Not enabled", INK_SOFT),
}


# Keys whose renderer draws its own heading above a chart.
SELF_HEADED = {
    "hydropathy_profile",
    "composition",
    "transmembrane_candidates",
}


def _count(container, *path):
    """Length of a list found by following ``path`` through dicts."""
    value = container
    for step in path:
        if not isinstance(value, dict):
            return 0
        value = value.get(step)
    return len(value) if isinstance(value, list) else 0


def summarise_prediction(key, prediction):
    """One-line result for a completed predictor, as in the web report."""
    if not isinstance(prediction, dict):
        return ""

    if key == "signalp":
        if not prediction.get("detected"):
            return "No signal peptide predicted."
        kind = prediction.get("signal_peptide_type") or "Signal peptide"
        after = prediction.get("cleavage_after")
        return (
            f"{kind}; cleavage after residue {after}."
            if after
            else f"{kind}."
        )

    if key == "deeptmhmm":
        parts = [f"Class {prediction.get('predicted_class')}"]
        helices = prediction.get("transmembrane_helices") or 0
        strands = prediction.get("beta_strands") or 0
        if helices:
            parts.append(f"{helices} transmembrane helices")
        if strands:
            parts.append(f"{strands} beta strands")
        return "; ".join(parts) + "."

    if key == "psortb":
        try:
            score = float(prediction.get("score"))
        except (TypeError, ValueError):
            return f"{prediction.get('localization')}."
        note = ", below the 7.50 confidence cut-off" if score < 7.5 else ""
        return (
            f"{prediction.get('localization')}, "
            f"score {score:.2f} of 10{note}."
        )

    if key == "epitopes":
        return (
            f"{_count(prediction, 'mhc_class_i', 'binders')} MHC-I and "
            f"{_count(prediction, 'mhc_class_ii', 'binders')} MHC-II binder "
            f"windows; {_count(prediction, 'b_cell', 'regions')} "
            "B-cell regions."
        )

    return ""


def generate_report_pdf(report: dict) -> BytesIO:
    """Generate a concise, chart-enhanced research report."""
    if not isinstance(report, dict):
        raise ValueError("A valid analysis report is required.")

    protein_analyses = report.get("protein_analyses")
    is_multi_report = (
        isinstance(protein_analyses, list)
        and len(protein_analyses) > 0
        and all(isinstance(item, dict) for item in protein_analyses)
    )

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=PAGE_MARGIN,
        leftMargin=PAGE_MARGIN,
        topMargin=19 * mm,
        bottomMargin=20 * mm,
        title="Reverse Vaccinology Research Report",
        author="ReverseVax",
    )

    styles = {}

    def add_style(name, **kwargs):
        styles[name] = ParagraphStyle(name=name, **kwargs)

    add_style(
        "Kicker",
        fontName=MONO, fontSize=7.5, leading=10, textColor=ACCENT,
        spaceBefore=3 * mm, spaceAfter=2 * mm,
    )
    add_style(
        "ReportTitle",
        fontName=SERIF_BOLD, fontSize=27, leading=30, textColor=INK,
        spaceAfter=4 * mm,
    )
    add_style(
        "PartTitle",
        fontName=SERIF_BOLD, fontSize=19, leading=23, textColor=INK,
        spaceAfter=3 * mm,
    )
    add_style(
        "SectionHeading",
        fontName=SERIF_BOLD, fontSize=15, leading=19, textColor=INK,
        spaceBefore=2.5 * mm, spaceAfter=3 * mm, keepWithNext=True,
    )
    add_style(
        "SubHeading",
        fontName=SANS_BOLD, fontSize=8, leading=11, textColor=INK_SOFT,
        spaceBefore=4 * mm, spaceAfter=1.5 * mm, keepWithNext=True,
    )
    add_style(
        "ReportBody",
        fontName=SERIF, fontSize=9.5, leading=13, textColor=INK,
        spaceAfter=3, wordWrap="LTR",
    )
    add_style(
        "SmallNote",
        fontName=SERIF_ITALIC, fontSize=8.5, leading=11.5,
        textColor=INK_SOFT, spaceAfter=3,
    )
    add_style(
        "Caption",
        fontName=SANS, fontSize=7.5, leading=10, textColor=INK_SOFT,
        spaceBefore=1.5 * mm, spaceAfter=3 * mm,
    )
    add_style(
        "TableHead",
        fontName=SANS_BOLD, fontSize=7.5, leading=9.5, textColor=INK_SOFT,
    )
    add_style(
        "TableText",
        fontName=SANS, fontSize=8, leading=10.5, textColor=INK,
    )
    add_style(
        "TableData",
        fontName=MONO, fontSize=7.8, leading=10.5, textColor=INK,
    )
    add_style(
        "PredictorName",
        fontName=SANS, fontSize=8, leading=10.5, textColor=INK_SOFT,
    )

    story = [
        HRFlowable(
            width="100%", thickness=2, color=INK,
            spaceBefore=0, spaceAfter=0,
        ),
        Paragraph("REVERSEVAX  \u00b7  EVIDENCE REPORT", styles["Kicker"]),
        Paragraph(
            "Reverse Vaccinology<br/>Research Report",
            styles["ReportTitle"],
        ),
        Paragraph(
            "Computational findings, evidence, interpretations and "
            "limitations. Predictions in this report are screens, not "
            "validation.",
            styles["SmallNote"],
        ),
        Spacer(1, 3 * mm),
    ]

    counters = {"section": 0, "figure": 0}
    # The report whose sections are being drawn: the whole report, or one
    # protein of a multi-FASTA report.
    current = {"source": report}

    def reset_counters():
        counters["section"] = 0
        counters["figure"] = 0

    def section_heading(title):
        """Rule, numbered kicker and heading, as in the web report."""
        counters["section"] += 1
        rule = HRFlowable(
            width="100%", thickness=0.75, color=INK,
            spaceBefore=6 * mm, spaceAfter=0,
        )
        rule.keepWithNext = True
        story.append(rule)
        story.append(Paragraph(
            f'<font name="{MONO}" size="8" color="{ACCENT_HEX}">'
            f'{counters["section"]:02d}</font>&nbsp;&nbsp;{escape(title)}',
            styles["SectionHeading"],
        ))

    def caption(text):
        counters["figure"] += 1
        return Paragraph(
            f'<font name="{MONO}" color="{ACCENT_HEX}">'
            f'Fig. {counters["figure"]}</font>&nbsp;&nbsp;{escape(text)}',
            styles["Caption"],
        )

    def scalar(value):
        if value is None:
            return "Not available"
        if isinstance(value, bool):
            return "Yes" if value else "No"
        if isinstance(value, float):
            return f"{value:.4f}".rstrip("0").rstrip(".")
        if isinstance(value, (dict, list, tuple)):
            return str(value)
        return str(value)

    def paragraph(value, style="ReportBody"):
        return Paragraph(escape(scalar(value)), styles[style])

    def head(*labels):
        return [Paragraph(escape(label), styles["TableHead"]) for label in labels]

    def cell(value, mono=None):
        """A table cell; numbers and sequences are set in the data face."""
        if mono is None:
            mono = (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
            )
        return Paragraph(
            escape(scalar(value)),
            styles["TableData" if mono else "TableText"],
        )

    def make_table(rows, widths=None):
        """A ruled table: no fills, a heavy rule above and below."""
        table = Table(
            rows,
            colWidths=widths,
            repeatRows=1,
            hAlign="LEFT",
            splitByRow=1,
        )
        table.setStyle(TableStyle([
            ("LINEABOVE", (0, 0), (-1, 0), 0.9, INK),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, INK),
            ("LINEBELOW", (0, 1), (-1, -1), 0.25, RULE),
            ("LINEBELOW", (0, -1), (-1, -1), 0.9, INK),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (0, -1), 0),
            ("LEFTPADDING", (1, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 3.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ]))
        return table

    def add_field_table(items):
        rows = [head("Field", "Value")]
        for key, value in items:
            rows.append([
                cell(str(key).replace("_", " ").title(), mono=False),
                cell(value),
            ])
        story.append(make_table(rows, [48 * mm, 112 * mm]))

    def add_conserved_regions_table(regions):
        if not regions:
            story.append(paragraph("No conserved regions were reported."))
            return

        rows = [head("Region", "Start", "End", "Length", "Consensus")]

        for index, region in enumerate(regions, start=1):
            start = region.get("start")
            end = region.get("end")
            length = region.get(
                "length",
                end - start + 1 if start is not None and end is not None else None,
            )
            consensus = region.get("consensus", region.get("sequence", "Not available"))

            rows.append([
                cell(index),
                cell(start),
                cell(end),
                cell(length),
                cell(consensus, mono=True),
            ])

        story.append(make_table(
            rows,
            [15 * mm, 18 * mm, 18 * mm, 18 * mm, 100 * mm],
        ))

    def add_peptide_candidates_table(candidates):
        story.append(paragraph(
            f"Total peptide candidate records: {len(candidates)}."
        ))

        if not candidates:
            story.append(paragraph("No peptide candidate records are available."))
            return

        rows = [head(
            "Start", "End", "Length", "Sequence", "GRAVY",
            "Net charge", "Transmembrane overlap",
        )]

        for candidate in candidates:
            rows.append([
                cell(candidate.get("start")),
                cell(candidate.get("end")),
                cell(candidate.get("length")),
                cell(candidate.get("sequence", "Not available"), mono=True),
                cell(candidate.get("gravy")),
                cell(candidate.get("net_charge")),
                cell(candidate.get("overlaps_transmembrane"), mono=False),
            ])

        story.append(make_table(
            rows,
            [13 * mm, 13 * mm, 15 * mm, 65 * mm, 18 * mm, 20 * mm, 32 * mm],
        ))

    def add_scalar_table(data):
        add_field_table(
            (key, value) for key, value in data.items() if key != "sequence"
        )

    def add_prediction_tools(source):
        """Which optional predictors ran, and why any did not."""
        measurements = source.get("measurements")
        predictions = (
            measurements.get("sequence_predictions")
            if isinstance(measurements, dict)
            else None
        )
        if not isinstance(predictions, dict):
            return False

        statuses = source.get("prediction_status")
        if not isinstance(statuses, dict):
            statuses = {}

        section_heading("Prediction Tools")
        note = paragraph(
            "Which optional external predictors ran for this report, and "
            "why any did not.",
            "SmallNote",
        )
        note.keepWithNext = True
        story.append(note)

        rows = [head("Tool", "State", "Result or reason")]

        for key, status_key, name, purpose in PREDICTORS:
            prediction = predictions.get(key)
            entry = statuses.get(status_key)
            state = (
                (entry or {}).get("status")
                if isinstance(entry, dict)
                else None
            ) or (
                prediction.get("status")
                if isinstance(prediction, dict)
                else None
            )
            if state not in STATE_LABELS:
                state = "not_enabled"

            label, colour = STATE_LABELS[state]
            message = (
                entry.get("message") if isinstance(entry, dict) else None
            ) or (
                prediction.get("message")
                if isinstance(prediction, dict)
                else None
            )

            if state == "completed":
                detail = summarise_prediction(key, prediction)
            elif state == "not_enabled":
                detail = "Not enabled on this server."
            else:
                detail = message or ""

            rows.append([
                Paragraph(
                    f"<b>{escape(name)}</b><br/>"
                    f'<font color="{INK_FAINT.hexval().replace("0x", "#")}">'
                    f"{escape(purpose)}</font>",
                    styles["TableText"],
                ),
                Paragraph(
                    f'<font color="{colour.hexval().replace("0x", "#")}">'
                    f"<b>{escape(label)}</b></font>",
                    styles["TableText"],
                ),
                cell(detail, mono=False),
            ])

        story.append(make_table(rows, [50 * mm, 26 * mm, 84 * mm]))
        return True

    def add_hydropathy_chart(profile):
        """Draw a vector chart from the actual profile points."""
        points = []
        for item in profile:
            if not isinstance(item, dict):
                continue
            try:
                x = float(item.get("start", len(points) + 1))
                y = float(item["hydropathy"])
                if x == x and y == y:
                    points.append((x, y))
            except (TypeError, ValueError, KeyError):
                continue

        if not points:
            story.append(paragraph(
                "Hydropathy profile unavailable: no valid profile points "
                "were supplied."
            ))
            return

        width, height = 480, 205
        left, right, top, bottom = 48, 16, 20, 35
        plot_width = width - left - right
        plot_height = height - top - bottom

        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(0.0, min(p[1] for p in points))
        max_y = max(0.0, max(p[1] for p in points))

        if min_x == max_x:
            max_x = min_x + 1
        if min_y == max_y:
            min_y -= 1
            max_y += 1

        pad_y = (max_y - min_y) * 0.08
        min_y -= pad_y
        max_y += pad_y

        def xy(x, y):
            px = left + (x - min_x) / (max_x - min_x) * plot_width
            py = bottom + (y - min_y) / (max_y - min_y) * plot_height
            return px, py

        drawing = Drawing(width, height)

        for fraction in (0, 0.5, 1):
            value = min_y + fraction * (max_y - min_y)
            py = bottom + fraction * plot_height
            drawing.add(Line(
                left, py, width - right, py,
                strokeColor=RULE, strokeWidth=0.5,
            ))
            drawing.add(String(
                left - 7, py - 3, f"{value:.2f}",
                textAnchor="end", fontName=MONO, fontSize=7,
                fillColor=INK_SOFT,
            ))

        if min_y <= 0 <= max_y:
            zero_y = xy(min_x, 0)[1]
            drawing.add(Line(
                left, zero_y, width - right, zero_y,
                strokeColor=INK, strokeWidth=0.8,
            ))

        mapped = [xy(x, y) for x, y in points]
        if len(mapped) > 1:
            drawing.add(PolyLine(
                [coordinate for point in mapped for coordinate in point],
                strokeColor=INK,
                strokeWidth=1.2,
            ))
        else:
            px, py = mapped[0]
            drawing.add(Rect(
                px - 2, py - 2, 4, 4,
                fillColor=INK, strokeColor=INK,
            ))

        drawing.add(String(
            width / 2, 7, "Window start position (residue)",
            textAnchor="middle", fontName=SANS, fontSize=8,
            fillColor=INK_SOFT,
        ))
        drawing.add(String(
            left, height - 9, "Hydropathy",
            fontName=SANS, fontSize=8, fillColor=INK_SOFT,
        ))

        values = [y for _, y in points]
        min_point = points[values.index(min(values))]
        max_point = points[values.index(max(values))]

        story.append(KeepTogether([
            Paragraph("Hydropathy Profile", styles["SubHeading"]),
            paragraph(
                f"{len(points)} valid windows. "
                f"Minimum: {min_point[1]:.3f} at residue "
                f"{min_point[0]:g}; maximum: {max_point[1]:.3f} "
                f"at residue {max_point[0]:g}.",
                "SmallNote",
            ),
            drawing,
            caption("Hydropathy profile along the sequence."),
            paragraph(
                "Interpretation depends on the profile method and window "
                "size. This chart alone does not establish membrane topology.",
                "SmallNote",
            ),
        ]))

    
    def add_composition_chart(composition):
        """Render composition chart and a combined count/percentage table."""
        if not isinstance(composition, dict):
            story.append(paragraph(
                "Amino-acid composition unavailable."
            ))
            return

        counts = composition.get("counts", {})
        sequence_length = composition.get("length")
        percentages = composition.get("percentages", {})

        if not isinstance(counts, dict):
            counts = {}
        if not isinstance(percentages, dict):
            percentages = {}

        residues = sorted(set(counts) | set(percentages))

        if not residues:
            story.append(paragraph(
                "Amino-acid counts and percentages were not supplied."
            ))
            return

        rows = [head("Residue", "Count", "Percentage")]

        if sequence_length is not None:
            story.append(paragraph(
                f"Sequence length: {sequence_length} amino acids."
            ))

        chart_values = []

        for residue in residues:
            count = counts.get(residue)
            percentage = percentages.get(residue)

            try:
                numeric_percentage = float(percentage)
                if (
                    numeric_percentage == numeric_percentage
                    and numeric_percentage >= 0
                ):
                    chart_values.append(
                        (str(residue), numeric_percentage)
                    )
            except (TypeError, ValueError):
                pass

            rows.append([
                cell(residue, mono=True),
                cell(count),
                cell(
                    f"{float(percentage):.2f}%"
                    if percentage is not None
                    else "Not available",
                    mono=percentage is not None,
                ),
            ])

        story.append(Paragraph(
            "Amino-acid Composition",
            styles["SubHeading"],
        ))

        if chart_values:
            chart_values.sort(key=lambda item: item[1], reverse=True)
            chart_values = chart_values[:10]

            width = 480
            row_height = 17
            height = max(55, 25 + row_height * len(chart_values))
            drawing = Drawing(width, height)

            label_width = 28
            bar_width = 330
            max_value = max(value for _, value in chart_values) or 1

            for index, (residue, value) in enumerate(chart_values):
                y = height - 23 - index * row_height
                drawing.add(String(
                    2, y, residue,
                    fontName=MONO,
                    fontSize=8,
                    fillColor=INK,
                ))
                drawing.add(Rect(
                    label_width,
                    y - 2,
                    bar_width * value / max_value,
                    9,
                    fillColor=WASH,
                    strokeColor=INK,
                    strokeWidth=0.6,
                ))
                drawing.add(String(
                    label_width + bar_width + 6,
                    y,
                    f"{value:.2f}%",
                    fontName=MONO,
                    fontSize=7.5,
                    fillColor=INK_SOFT,
                ))

            story.append(drawing)
            story.append(caption(
                "Top 10 residues by reported percentage."
            ))

        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            "Residue Counts and Percentages",
            styles["SubHeading"],
        ))
        composition_table = make_table(
            rows,
            [45 * mm, 45 * mm, 70 * mm],
        )
        composition_table.hAlign = "LEFT"
        story.append(composition_table)

    
    def add_conservation_chart(conservation):
        """Plot majority-residue frequency when alignment columns exist."""
        if not isinstance(conservation, dict):
            story.append(paragraph(
                "Conservation analysis unavailable: no conservation "
                "data was supplied."
            ))
            return

        status = conservation.get("status", "unknown")
        columns = conservation.get("columns") or []

        if status == "not_performed":
            story.append(paragraph(
                "Conservation analysis was not performed. No alignment "
                "profile is available for plotting."
            ))
            return

        if not columns:
            story.append(paragraph(
                "Conservation profile unavailable: no alignment columns "
                "were supplied."
            ))
            return

        points = []
        for column in columns:
            if not isinstance(column, dict):
                continue
            try:
                position = float(column["position"])
                frequency = float(column["conservation_percentage"])
                if (
                    position == position
                    and frequency == frequency
                    and 0 <= frequency <= 100
                ):
                    points.append((position, frequency))
            except (KeyError, TypeError, ValueError):
                continue

        points.sort(key=lambda item: item[0])

        if not points:
            story.append(paragraph(
                "Conservation profile unavailable: no valid positional "
                "frequency values were supplied."
            ))
            return

        width, height = 480, 190
        left, right, top, bottom = 48, 16, 18, 32
        plot_width = width - left - right
        plot_height = height - top - bottom

        min_x = min(x for x, _ in points)
        max_x = max(x for x, _ in points)
        if min_x == max_x:
            max_x = min_x + 1

        def xy(position, frequency):
            px = left + (
                (position - min_x) / (max_x - min_x)
            ) * plot_width
            py = bottom + (frequency / 100) * plot_height
            return px, py

        drawing = Drawing(width, height)

        for frequency in (0, 50, 100):
            py = bottom + (frequency / 100) * plot_height
            drawing.add(Line(
                left, py, width - right, py,
                strokeColor=RULE,
                strokeWidth=0.5,
            ))
            drawing.add(String(
                left - 7, py - 3, f"{frequency}%",
                textAnchor="end",
                fontName=MONO,
                fontSize=7,
                fillColor=INK_SOFT,
            ))

        mapped = [xy(position, frequency) for position, frequency in points]

        if len(mapped) > 1:
            drawing.add(PolyLine(
                [coordinate for point in mapped for coordinate in point],
                strokeColor=INK,
                strokeWidth=1.1,
            ))
        else:
            px, py = mapped[0]
            drawing.add(Rect(
                px - 2, py - 2, 4, 4,
                fillColor=INK,
                strokeColor=INK,
            ))

        drawing.add(String(
            width / 2, 7,
            "Alignment position (residue column)",
            textAnchor="middle",
            fontName=SANS,
            fontSize=8,
            fillColor=INK_SOFT,
        ))

        story.append(KeepTogether([
            Paragraph(
                "Per-position Conservation Profile",
                styles["SubHeading"],
            ),
            paragraph(
                f"{len(points)} alignment positions plotted. "
                "Values represent the percentage of non-gap residues "
                "matching the most frequent residue in each column.",
                "SmallNote",
            ),
            drawing,
            caption("Majority-residue frequency per alignment position."),
            paragraph(
                "Majority-residue frequency is a descriptive alignment "
                "measure, not a standalone evolutionary conservation "
                "score. Columns containing only gaps have no plotted value.",
                "SmallNote",
            ),
        ]))

    
    def add_transmembrane_map(candidates, sequence_length):
        """Visualize candidate regions along the full protein sequence."""
        if not isinstance(candidates, list) or not candidates:
            story.append(paragraph(
                "No transmembrane candidates are available to visualize. "
                "This does not establish that the protein lacks "
                "transmembrane regions."
            ))
            return

        try:
            sequence_length = int(sequence_length)
        except (TypeError, ValueError):
            sequence_length = 0

        if sequence_length <= 0:
            story.append(paragraph(
                "Transmembrane map unavailable: protein sequence length "
                "is missing or invalid."
            ))
            return

        valid_regions = []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            try:
                start = int(candidate["start"])
                end = int(candidate["end"])
            except (KeyError, TypeError, ValueError):
                continue

            if start < 1 or end < start or end > sequence_length:
                continue

            valid_regions.append({
                "start": start,
                "end": end,
                "classification": str(
                    candidate.get("classification", "unclassified")
                ),
                "hydropathy_matches": candidate.get(
                    "hydropathy_matches"
                ),
                "length_matches": candidate.get("length_matches"),
            })

        if not valid_regions:
            story.append(paragraph(
                "Transmembrane map unavailable: no candidates contain "
                "valid start and end positions within the protein sequence."
            ))
            return

        width = 480
        row_height = 27
        top = 24
        bottom = 25
        height = top + bottom + row_height * len(valid_regions)
        left = 48
        right = 14
        track_width = width - left - right

        drawing = Drawing(width, height)

        drawing.add(String(
            left, height - 13,
            f"Residue positions (1–{sequence_length})",
            fontName=SANS,
            fontSize=8,
            fillColor=INK_SOFT,
        ))

        for index, region in enumerate(valid_regions):
            y = height - top - (index + 1) * row_height

            drawing.add(Rect(
                left, y, track_width, 9,
                fillColor=WASH,
                strokeColor=RULE,
                strokeWidth=0.4,
            ))

            x1 = left + (
                (region["start"] - 1) / sequence_length
            ) * track_width
            x2 = left + (
                region["end"] / sequence_length
            ) * track_width
            bar_width = max(2, x2 - x1)

            drawing.add(Rect(
                x1, y, bar_width, 9,
                fillColor=ACCENT,
                strokeColor=INK,
                strokeWidth=0.6,
            ))

            drawing.add(String(
                2, y + 1,
                f"{region['start']}-{region['end']}",
                fontName=MONO,
                fontSize=7,
                fillColor=INK,
            ))

            label = (
                f"Candidate {index + 1}: "
                f"{region['classification']}"
            )
            drawing.add(String(
                left, y - 9, label[:72],
                fontName=SANS,
                fontSize=7,
                fillColor=INK_SOFT,
            ))

        story.append(KeepTogether([
            Paragraph(
                "Transmembrane Candidate Map",
                styles["SubHeading"],
            ),
            paragraph(
                "Highlighted intervals show the positions of candidate "
                "regions along the protein sequence. They are predictions, "
                "not confirmation of membrane topology.",
                "SmallNote",
            ),
            drawing,
            caption("Candidate transmembrane regions along the sequence."),
        ]))

    def add_nested(value, key=None):
        if key == "sequence":
            sequence = str(value or "")
            if not sequence:
                story.append(paragraph("Sequence: Not available"))
            else:
                preview = sequence[:36]
                suffix = "…" if len(sequence) > 36 else ""
                story.append(paragraph(
                    f"Sequence omitted from main report. Length: "
                    f"{len(sequence)} residues. N-terminal excerpt: "
                    f"{preview}{suffix}. The complete sequence remains "
                    f"available in the underlying analysis data."
                ))
            return

        if key == "hydropathy_profile" and isinstance(value, list):
            add_hydropathy_chart(value)
            return

        if key == "conservation" and isinstance(value, dict):
            add_conservation_chart(value)
            summary = value.get("summary")
            if summary is not None:
                story.append(Paragraph(
                    "Conservation Summary",
                    styles["SubHeading"],
                ))
                add_nested(summary)
            regions = value.get("regions") or []
            story.append(Paragraph(
                "Conserved Regions",
                styles["SubHeading"],
            ))
            add_nested(regions)
            return

        
        if key == "transmembrane_candidates" and isinstance(value, list):
            protein = current["source"].get("protein", {})
            sequence_length = (
                protein.get("length")
                if isinstance(protein, dict)
                else None
            )
            add_transmembrane_map(value, sequence_length)

            if value:
                story.append(Paragraph(
                    "Candidate Details",
                    styles["SubHeading"],
                ))
                for index, candidate in enumerate(value, start=1):
                    story.append(Paragraph(
                        f"Candidate {index}",
                        styles["SubHeading"],
                    ))
                    add_nested(candidate)
            return

        if key == "composition" and isinstance(value, dict):
            add_composition_chart(value)
            return

        if key == "peptide_candidates" and isinstance(value, list):
            add_peptide_candidates_table(value)
            return

        if (
            key == "limitations"
            and isinstance(value, list)
            and value
            and all(not isinstance(item, (dict, list)) for item in value)
        ):
            rows = [[paragraph(item)] for item in value]
            notes = Table(rows, colWidths=[CONTENT_WIDTH], hAlign="LEFT")
            notes.setStyle(TableStyle([
                ("LINEBEFORE", (0, 0), (0, -1), 2, ACCENT),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            story.append(notes)
            return


        if isinstance(value, dict):
            if not value:
                story.append(paragraph("No details available."))
                return

            scalar_only = all(
                not isinstance(item, (dict, list))
                for item in value.values()
            )

            if scalar_only:
                add_field_table(value.items())
                return

            for child_key, item in value.items():
                if child_key == "sequence":
                    add_nested(item, key=child_key)
                    continue

                if child_key == "sequence_predictions" and isinstance(item, dict):
                    # The four external predictors are summarised in the
                    # Prediction Tools section; keep the built-in results.
                    item = {
                        name: result
                        for name, result in item.items()
                        if name not in {key for key, *_ in PREDICTORS}
                    }
                    if not item:
                        continue

                if child_key in SELF_HEADED and (
                    isinstance(item, (list, dict))
                ):
                    add_nested(item, key=child_key)
                    continue

                story.append(Paragraph(
                    escape(str(child_key).replace("_", " ").title()),
                    styles["SubHeading"],
                ))
                add_nested(item, key=child_key)
            return

        if isinstance(value, list):
            if not value:
                story.append(paragraph("None available."))
                return

            # Raw profile points are handled by the chart above.
            # Keep other lists readable without silently implying that
            # an empty list is evidence of a negative result.
            if all(not isinstance(item, (dict, list)) for item in value):
                for item in value:
                    story.append(Paragraph(
                        f"• {escape(scalar(item))}",
                        styles["ReportBody"],
                    ))
                return

            for index, item in enumerate(value, start=1):
                if index > 30:
                    story.append(paragraph(
                        f"{len(value) - 30} additional records omitted "
                        f"from the PDF display. They remain in the "
                        f"underlying report data."
                    ))
                    break
                story.append(Paragraph(
                    f"Record {index}", styles["SubHeading"]
                ))
                add_nested(item)
            return

        story.append(paragraph(value))

    # Same order as the report on screen.
    sections = [
        ("metadata", "Report Metadata"),
        ("protein", "Protein Characteristics"),
        ("measurements", "Measurements and Charts"),
        ("prediction_tools", "Prediction Tools"),
        ("conservation", "Conservation Analysis"),
        ("evidence", "Evidence"),
        ("interpretations", "Interpretations"),
        ("candidate_assessment", "Candidate Assessment"),
        ("limitations", "Limitations"),
        ("peptide_candidates", "Peptide Candidates"),
    ]

    def render_sections(source, skip=()):
        current["source"] = source

        for key, title in sections:
            if key in skip:
                continue

            if key == "prediction_tools":
                if add_prediction_tools(source):
                    story.append(Spacer(1, 3 * mm))
                continue

            if key not in source:
                continue

            section_heading(title)
            content = source[key]

            if key == "protein" and isinstance(content, dict):
                add_scalar_table(content)

                if content.get("sequence"):
                    story.append(Spacer(1, 2 * mm))
                    add_nested(content["sequence"], key="sequence")
            else:
                add_nested(content, key=key)

            story.append(Spacer(1, 3 * mm))

    if is_multi_report:
        shared_conservation = report.get("conservation", {})

        story.append(Paragraph(
            "Multi-FASTA Comparative Analysis",
            styles["PartTitle"],
        ))

        section_heading("Shared Alignment and Conservation")

        sequence_count = shared_conservation.get("sequence_count")
        alignment_length = shared_conservation.get("alignment_length")
        mean_identity = shared_conservation.get("mean_identity")
        conservation_percentage = shared_conservation.get(
            "conservation_percentage"
        )

        summary_rows = [head("Measurement", "Result")]

        for label, value in [
            ("Sequences analyzed", sequence_count),
            ("Alignment length", alignment_length),
            ("Mean identity", mean_identity),
            ("Conservation percentage", conservation_percentage),
        ]:
            if value is not None:
                summary_rows.append([
                    cell(label, mono=False),
                    cell(str(value), mono=True),
                ])

        if len(summary_rows) > 1:
            story.append(make_table(
                summary_rows,
                [75 * mm, 75 * mm],
            ))

        conserved_regions = report.get("conserved_regions") or []

        story.append(Paragraph(
            "Conserved Regions",
            styles["SubHeading"],
        ))

        add_conserved_regions_table(conserved_regions)

        story.append(Spacer(1, 5 * mm))

        for index, protein_report in enumerate(
            protein_analyses,
            start=1,
        ):
            protein = protein_report.get("protein", {})
            protein_id = (
                protein.get("id")
                or protein_report.get("protein_id")
                or f"Protein {index}"
            )

            reset_counters()
            story.append(PageBreak())
            story.append(Paragraph(
                f"Protein Analysis: {escape(str(protein_id))}",
                styles["PartTitle"],
            ))

            render_sections(protein_report, skip=("conservation",))
    else:
        render_sections(report)

    def draw_page(canvas, doc):
        page_width, page_height = A4
        canvas.saveState()
        canvas.setFillColor(PAPER)
        canvas.rect(0, 0, page_width, page_height, stroke=0, fill=1)
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.5)
        canvas.line(
            PAGE_MARGIN, 14 * mm,
            page_width - PAGE_MARGIN, 14 * mm,
        )
        canvas.setFont(MONO, 7)
        canvas.setFillColor(INK_FAINT)
        canvas.drawString(
            PAGE_MARGIN, 9.5 * mm,
            "ReverseVax  \u00b7  Evidence report  \u00b7  "
            "predictions are screens, not validation",
        )
        canvas.drawRightString(
            page_width - PAGE_MARGIN, 9.5 * mm,
            f"Page {doc.page}",
        )
        canvas.restoreState()

    document.build(
        story,
        onFirstPage=draw_page,
        onLaterPages=draw_page,
    )
    buffer.seek(0)
    return buffer
