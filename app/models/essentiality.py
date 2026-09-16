from dataclasses import dataclass


@dataclass
class EssentialityEvidence:
    gene_id: str
    organism: str
    essentiality_status: str
    source: str
    confidence: str
    description: str

    def to_dict(self) -> dict:
        return {
            "gene_id": self.gene_id,
            "organism": self.organism,
            "essentiality_status": self.essentiality_status,
            "source": self.source,
            "confidence": self.confidence,
            "description": self.description,
        }