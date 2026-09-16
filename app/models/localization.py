from dataclasses import dataclass


@dataclass
class LocalizationEvidence:
    location: str
    source: str
    confidence: str
    description: str

    def to_dict(self) -> dict:
        """
        Convert localization evidence into a dictionary.
        """

        return {
            "location": self.location,
            "source": self.source,
            "confidence": self.confidence,
            "description": self.description,
        }