from flask import Flask, request

from app.analysis.pipeline import analyze_protein
from app.reporting.report import generate_protein_report


def create_app():
    app = Flask(__name__)

    @app.post("/api/analyze")
    def analyze():
        data = request.get_json(silent=True)

        if not data:
            return {"error": "JSON request body is required."}, 400
        if "sequence" not in data:
            return {"error": "Sequence is required."}, 400

        try:
            result = analyze_protein(
                data["sequence"],
                protein_id=data.get("protein_id"),
            )
        except ValueError as error:
            return {"error": str(error)}, 400
        report = generate_protein_report(result)

        return report, 200

    return app