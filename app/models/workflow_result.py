from dataclasses import dataclass

from app.models.conservation import ConservationResult


@dataclass
class AnalysisWorkflowResult:
    records: list[dict]
    alignment: list[str]
    conservation: ConservationResult

    def to_dict(self) -> dict:
        return {
            "records": self.records,
            "alignment": self.alignment,
            "conservation": self.conservation.to_dict(),
        }