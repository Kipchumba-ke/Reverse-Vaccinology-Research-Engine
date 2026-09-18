from dataclasses import dataclass


@dataclass
class EvidenceAssessment:
    supporting_evidence: list[str]
    concerns: list[str]
    missing_evidence: list[str]

    def to_dict(self) -> dict:
        return {
            "supporting_evidence": self.supporting_evidence,
            "concerns": self.concerns,
            "missing_evidence": self.missing_evidence,
        }