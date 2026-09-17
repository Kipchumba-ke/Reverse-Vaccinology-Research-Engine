from dataclasses import dataclass


@dataclass
class CandidateAssessment:
    status: str
    supporting_evidence: list[str]
    concerns: list[str]
    missing_evidence: list[str]

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "supporting_evidence": self.supporting_evidence,
            "concerns": self.concerns,
            "missing_evidence": self.missing_evidence,
        }