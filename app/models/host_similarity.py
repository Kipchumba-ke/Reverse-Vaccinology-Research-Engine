from dataclasses import dataclass


@dataclass
class HostSimilarityEvidence:
    target_id: str
    host_id: str
    similarity_method: str
    identity_percentage: float
    alignment_length: int
    query_coverage_percentage: float
    subject_coverage_percentage: float
    e_value: float
    source: str
    confidence: str
    description: str

    def to_dict(self) -> dict:
        return {
            "target_id": self.target_id,
            "host_id": self.host_id,
            "similarity_method": self.similarity_method,
            "identity_percentage": self.identity_percentage,
            "alignment_length": self.alignment_length,
            "query_coverage_percentage": (
                self.query_coverage_percentage
            ),
            "subject_coverage_percentage": (
                self.subject_coverage_percentage
            ),
            "e_value": self.e_value,
            "source": self.source,
            "confidence": self.confidence,
            "description": self.description,
        }