from dataclasses import dataclass


@dataclass
class Evidence:
    category: str
    finding: str
    interpretation: str
    confidence: str

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "finding": self.finding,
            "interpretation": self.interpretation,
            "confidence": self.confidence,
        }