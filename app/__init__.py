from flask import Flask, request

from app.analysis.pipeline import analyze_protein
from app.reporting.report import generate_protein_report
from app.input.fasta import parse_fasta, parse_fasta_records
from app.analysis.workflow import analyze_fasta_records


def create_app():
    app = Flask(__name__)

    @app.post("/api/analyze")
    def analyze():
        if "file" in request.files:
            uploaded_file = request.files["file"]

            if not uploaded_file.filename:
                return {"error": "FASTA file is required."}, 400

            try:
                fasta_text = uploaded_file.read().decode("utf-8")
                records = parse_fasta_records(fasta_text)

                if len(records) == 1:
                    record = records[0]
                    result = analyze_protein(
                        record["sequence"],
                        protein_id=record["id"],
                    )
                    report = generate_protein_report(result)
                    return report, 200

                workflow_result = analyze_fasta_records(records)
                return workflow_result.to_dict(), 200

            except (UnicodeDecodeError, ValueError) as error:
                return {"error": str(error)}, 400
        data = request.get_json(silent=True)

        if not data:
            return {"error": "JSON request body is required."}, 400
        if "sequence" not in data:
            return {"error": "Sequence is required."}, 400

        try:
            result = analyze_protein(
                data["sequence"],
                protein_id=data.get("protein_id"),
                protein_name=data.get("protein_name"),
                organism=data.get("organism"),
                accession=data.get("accession"),
            )
        except ValueError as error:
            return {"error": str(error)}, 400
        report = generate_protein_report(result)

        return report, 200

    return app