from flask import Flask, request

from app.services.analysis_service import analyze_sequence
from app.input.fasta import parse_fasta_records
from app.analysis.workflow import analyze_fasta_records
from werkzeug.exceptions import RequestEntityTooLarge


def create_app():
    app = Flask(__name__)
    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_entity_too_large(error):
        return {"error": "Request payload is too large."}, 413

    @app.post("/api/analyze")
    @app.post("/api/v1/analyze")
    def analyze():
        if "file" in request.files:
            uploaded_file = request.files["file"]

            if not uploaded_file.filename:
                return {"error": "FASTA file is required."}, 400

            filename = uploaded_file.filename.lower()
            if not filename.endswith((".fasta", ".fa", ".fna")):
                return {
                    "error": "Unsupported file type. FASTA files are required."
                }, 400

            try:
                fasta_text = uploaded_file.read().decode("utf-8")
                records = parse_fasta_records(fasta_text)

                if len(records) == 1:
                    record = records[0]
                    result = analyze_sequence(
                        record["sequence"],
                        protein_id=record["id"],
                        protein_name=record["description"],
                        organism=record["organism"],
                        accession=record["accession"],
                    )
                    return result, 200

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
            report = analyze_sequence(
                data["sequence"],
                protein_id=data.get("protein_id"),
                protein_name=data.get("protein_name"),
                organism=data.get("organism"),
                accession=data.get("accession"),
            )
        except (TypeError, ValueError) as error:
            return {"error": str(error)}, 400
        

        return report, 200

    return app