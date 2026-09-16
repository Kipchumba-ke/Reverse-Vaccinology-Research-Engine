from dataclasses import dataclass


@dataclass
class ConservationResult:
    sequence_count: int
    alignment_length: int
    mean_identity: float
    conserved_positions: int
    conservation_percentage: float

    def to_dict(self) -> dict:
        """
        Convert the conservation result into a dictionary.
        """

        return {
            "sequence_count": self.sequence_count,
            "alignment_length": self.alignment_length,
            "mean_identity": self.mean_identity,
            "conserved_positions": self.conserved_positions,
            "conservation_percentage": (
                self.conservation_percentage
            ),
        }