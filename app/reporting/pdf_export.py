
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.graphics.shapes import Drawing, Line, PolyLine, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


NAVY = colors.HexColor("#17365D")
TEAL = colors.HexColor("#167D75")
PALE_BLUE = colors.HexColor("#EAF2F8")
LIGHT_GREY = colors.HexColor("#E5E7EB")
DARK_GREY = colors.HexColor("#4B5563")


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
        rightMargin=17 * mm,
        leftMargin=17 * mm,
        topMargin=19 * mm,
        bottomMargin=18 * mm,
        title="Reverse Vaccinology Research Report",
        author="Reverse Vaccinology Research Engine",
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontSize=21,
        leading=26,
        alignment=TA_CENTER,
        textColor=NAVY,
        spaceAfter=8 * mm,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        textColor=NAVY,
        spaceBefore=5 * mm,
        spaceAfter=3 * mm,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="SubHeading",
        parent=styles["Heading3"],
        fontSize=10,
        leading=13,
        textColor=TEAL,
        spaceBefore=3 * mm,
        spaceAfter=2 * mm,
        keepWithNext=True,
    ))
    styles.add(ParagraphStyle(
        name="ReportBody",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=11,
        spaceAfter=3,
        wordWrap="LTR",
    ))
    styles.add(ParagraphStyle(
        name="SmallNote",
        parent=styles["BodyText"],
        fontSize=7.5,
        leading=10,
        textColor=DARK_GREY,
        spaceAfter=3,
    ))

    story = [
        Paragraph(
            "Reverse Vaccinology<br/>Research Report",
            styles["ReportTitle"],
        ),
        Paragraph(
            "Computational findings, evidence, interpretations and limitations",
            styles["SmallNote"],
        ),
        Spacer(1, 4 * mm),
    ]

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

    def make_table(rows, widths=None):
        table = Table(
            rows,
            colWidths=widths,
            repeatRows=1,
            hAlign="LEFT",
            splitByRow=1,
        )
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PALE_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), NAVY),
            ("GRID", (0, 0), (-1, -1), 0.35, LIGHT_GREY),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return table

    def add_conserved_regions_table(regions):
        if not regions:
            story.append(paragraph("No conserved regions were reported."))
            return

        rows = [[
            paragraph("Region"),
            paragraph("Start"),
            paragraph("End"),
            paragraph("Length"),
            paragraph("Consensus"),
        ]]

        for index, region in enumerate(regions, start=1):
            start = region.get("start")
            end = region.get("end")
            length = region.get(
                "length",
                end - start + 1 if start is not None and end is not None else None,
            )
            consensus = region.get("consensus", region.get("sequence", "Not available"))

            rows.append([
                paragraph(index),
                paragraph(start),
                paragraph(end),
                paragraph(length),
                paragraph(consensus),
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

        rows = [[
            paragraph("Start"),
            paragraph("End"),
            paragraph("Length"),
            paragraph("Sequence"),
            paragraph("GRAVY"),
            paragraph("Net charge"),
            paragraph("Transmembrane overlap"),
        ]]

        for candidate in candidates:
            rows.append([
                paragraph(candidate.get("start")),
                paragraph(candidate.get("end")),
                paragraph(candidate.get("length")),
                paragraph(candidate.get("sequence", "Not available")),
                paragraph(candidate.get("gravy")),
                paragraph(candidate.get("net_charge")),
                paragraph(candidate.get("overlaps_transmembrane")),
            ])

        story.append(make_table(
            rows,
            [13 * mm, 13 * mm, 15 * mm, 65 * mm, 18 * mm, 20 * mm, 35 * mm],
        ))

    def add_scalar_table(data):
        rows = [[
            Paragraph("<b>Field</b>", styles["ReportBody"]),
            Paragraph("<b>Value</b>", styles["ReportBody"]),
        ]]
        for key, value in data.items():
            if key == "sequence":
                continue
            rows.append([
                paragraph(str(key).replace("_", " ").title()),
                paragraph(value),
            ])
        story.append(make_table(rows, [48 * mm, 112 * mm]))

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
                strokeColor=LIGHT_GREY, strokeWidth=0.5,
            ))
            drawing.add(String(
                left - 7, py - 3, f"{value:.2f}",
                textAnchor="end", fontSize=7, fillColor=DARK_GREY,
            ))

        if min_y <= 0 <= max_y:
            zero_y = xy(min_x, 0)[1]
            drawing.add(Line(
                left, zero_y, width - right, zero_y,
                strokeColor=DARK_GREY, strokeWidth=0.8,
            ))

        mapped = [xy(x, y) for x, y in points]
        if len(mapped) > 1:
            drawing.add(PolyLine(
                [coordinate for point in mapped for coordinate in point],
                strokeColor=TEAL,
                strokeWidth=1.2,
            ))
        else:
            px, py = mapped[0]
            drawing.add(Rect(
                px - 2, py - 2, 4, 4,
                fillColor=TEAL, strokeColor=TEAL,
            ))

        drawing.add(String(
            width / 2, 7, "Window start position (residue)",
            textAnchor="middle", fontSize=8, fillColor=DARK_GREY,
        ))
        drawing.add(String(
            5, height / 2, "Hydropathy",
            fontSize=8, fillColor=DARK_GREY,
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

        rows = [[
            Paragraph("<b>Residue</b>", styles["ReportBody"]),
            Paragraph("<b>Count</b>", styles["ReportBody"]),
            Paragraph("<b>Percentage</b>", styles["ReportBody"]),
        ]]

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
                paragraph(residue),
                paragraph(count),
                paragraph(
                    f"{float(percentage):.2f}%"
                    if percentage is not None
                    else "Not available"
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
                    fontSize=8,
                    fillColor=NAVY,
                ))
                drawing.add(Rect(
                    label_width,
                    y - 2,
                    bar_width * value / max_value,
                    9,
                    fillColor=TEAL,
                    strokeColor=None,
                ))
                drawing.add(String(
                    label_width + bar_width + 6,
                    y,
                    f"{value:.2f}%",
                    fontSize=7.5,
                    fillColor=DARK_GREY,
                ))

            story.append(paragraph(
                "Top 10 residues by reported percentage.",
                "SmallNote",
            ))
            story.append(drawing)

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
                strokeColor=LIGHT_GREY,
                strokeWidth=0.5,
            ))
            drawing.add(String(
                left - 7, py - 3, f"{frequency}%",
                textAnchor="end",
                fontSize=7,
                fillColor=DARK_GREY,
            ))

        mapped = [xy(position, frequency) for position, frequency in points]

        if len(mapped) > 1:
            drawing.add(PolyLine(
                [coordinate for point in mapped for coordinate in point],
                strokeColor=TEAL,
                strokeWidth=1.1,
            ))
        else:
            px, py = mapped[0]
            drawing.add(Rect(
                px - 2, py - 2, 4, 4,
                fillColor=TEAL,
                strokeColor=TEAL,
            ))

        drawing.add(String(
            width / 2, 7,
            "Alignment position (residue column)",
            textAnchor="middle",
            fontSize=8,
            fillColor=DARK_GREY,
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
            fontSize=8,
            fillColor=DARK_GREY,
        ))

        for index, region in enumerate(valid_regions):
            y = height - top - (index + 1) * row_height

            drawing.add(Rect(
                left, y, track_width, 9,
                fillColor=PALE_BLUE,
                strokeColor=LIGHT_GREY,
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
                fillColor=TEAL,
                strokeColor=TEAL,
            ))

            drawing.add(String(
                2, y + 1,
                f"{region['start']}-{region['end']}",
                fontSize=7,
                fillColor=NAVY,
            ))

            label = (
                f"Candidate {index + 1}: "
                f"{region['classification']}"
            )
            drawing.add(String(
                left, y - 9, label[:72],
                fontSize=7,
                fillColor=DARK_GREY,
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
            protein = report.get("protein", {})
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


        if isinstance(value, dict):
            if not value:
                story.append(paragraph("No details available."))
                return

            scalar_only = all(
                not isinstance(item, (dict, list))
                for item in value.values()
            )

            if scalar_only:
                rows = [[
                    Paragraph("<b>Field</b>", styles["ReportBody"]),
                    Paragraph("<b>Value</b>", styles["ReportBody"]),
                ]]
                for child_key, item in value.items():
                    rows.append([
                        paragraph(str(child_key).replace("_", " ").title()),
                        paragraph(item),
                    ])
                story.append(make_table(rows, [48 * mm, 112 * mm]))
                return

            for child_key, item in value.items():
                if child_key == "sequence":
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

    sections = [
        ("metadata", "Report Metadata"),
        ("protein", "Protein Characteristics"),
        ("measurements", "Measurements and Charts"),
        ("peptide_candidates", "Peptide Candidates"),
        ("conservation", "Conservation Analysis"),
        ("evidence", "Evidence"),
        ("interpretations", "Interpretations"),
        ("candidate_assessment", "Candidate Assessment"),
        ("limitations", "Limitations"),
    ]

    if is_multi_report:
        shared_conservation = report.get("conservation", {})
        records = report.get("records", [])

        story.append(Paragraph(
            "Multi-FASTA Comparative Analysis",
            styles["ReportTitle"],
        ))

        story.append(Paragraph(
            "Shared Alignment and Conservation",
            styles["SectionHeading"],
        ))

        sequence_count = shared_conservation.get("sequence_count")
        alignment_length = shared_conservation.get("alignment_length")
        mean_identity = shared_conservation.get("mean_identity")
        conservation_percentage = shared_conservation.get(
            "conservation_percentage"
        )

        summary_rows = [["Measurement", "Result"]]

        for label, value in [
            ("Sequences analyzed", sequence_count),
            ("Alignment length", alignment_length),
            ("Mean identity", mean_identity),
            ("Conservation percentage", conservation_percentage),
        ]:
            if value is not None:
                summary_rows.append([label, str(value)])

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
            report = protein_report

            protein = report.get("protein", {})
            protein_id = (
                protein.get("id")
                or report.get("protein_id")
                or f"Protein {index}"
            )

            story.append(PageBreak())
            story.append(Paragraph(
                f"Protein Analysis: {escape(str(protein_id))}",
                styles["ReportTitle"],
            ))

            for key, title in sections:
                if key == "conservation":
                    continue

                if key not in report:
                    continue

                story.append(Paragraph(
                    escape(title),
                    styles["SectionHeading"],
                ))

                content = report[key]

                if key == "protein" and isinstance(content, dict):
                    add_scalar_table(content)

                    if content.get("sequence"):
                        add_nested(
                            content["sequence"],
                            key="sequence",
                        )
                else:
                    add_nested(content, key=key)

                story.append(Spacer(1, 4 * mm))

    else:
        for key, title in sections:
            if key not in report:
                continue

            story.append(Paragraph(
                escape(title),
                styles["SectionHeading"],
            ))

            content = report[key]

            if key == "protein" and isinstance(content, dict):
                add_scalar_table(content)

                if content.get("sequence"):
                    add_nested(
                        content["sequence"],
                        key="sequence",
                    )
            else:
                add_nested(content, key=key)

            story.append(Spacer(1, 4 * mm))

    def draw_page(canvas, doc):
        canvas.saveState()
        page_width, _ = A4
        canvas.setStrokeColor(LIGHT_GREY)
        canvas.line(
            17 * mm, 13 * mm,
            page_width - 17 * mm, 13 * mm,
        )
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(DARK_GREY)
        canvas.drawString(
            17 * mm, 8 * mm,
            "Reverse Vaccinology Research Engine | Research report",
        )
        canvas.drawRightString(
            page_width - 17 * mm, 8 * mm,
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
