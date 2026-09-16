from dataclasses import dataclass
from app.models.localization import LocalizationEvidence

@dataclass
class ProteinAnalysisResult:
    sequence: str
    length: int
    composition: dict
    molecular_weight: float
    gravy: float
    isoelectric_point: float
    charge_and_hydrophobicity: dict
    hydropathy_profile: list[dict]
    hydrophobic_regions: list[dict]
    transmembrane_candidates: list[dict]
    localization_evidence: list[LocalizationEvidence]


    def to_dict(self) -> dict:
        """
        Convert the analysis result into a dictionary.
        """

        return {
            "sequence": self.sequence,
            "length": self.length,
            "composition": self.composition,
            "molecular_weight": self.molecular_weight,
            "gravy": self.gravy,
            "isoelectric_point": self.isoelectric_point,
            "charge_and_hydrophobicity": (
                self.charge_and_hydrophobicity
            ),
            "hydropathy_profile": self.hydropathy_profile,
            "hydrophobic_regions": self.hydrophobic_regions,
            "transmembrane_candidates": (
                self.transmembrane_candidates
            ),
            "localization_evidence": [
                evidence.to_dict()
                for evidence in self.localization_evidence
            ],
        }