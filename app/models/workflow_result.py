from dataclasses import dataclass

from app.models.analysis_result import ProteinAnalysisResult
from app.models.conservation import ConservationResult


@dataclass
class AnalysisWorkflowResult:
    records: list[dict]
    protein_analyses: list[ProteinAnalysisResult]
    alignment: list[str]
    conservation: ConservationResult
    conserved_regions: list[dict]

    def to_dict(self) -> dict:
        return {
            "records": self.records,
            "protein_analyses": [
                analysis.to_dict()
                for analysis in self.protein_analyses
            ],
            "alignment": self.alignment,
            "conservation": self.conservation.to_dict(),
            "conserved_regions": self.conserved_regions,
        }