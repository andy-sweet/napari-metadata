from enum import Enum, auto
from typing import List


class SpaceUnits(Enum):
    """Supported units for a spatial axis."""

    NONE = auto()
    NANOMETERS = auto()
    MICROMETERS = auto()
    MILLIMETERS = auto()
    CENTIMETERS = auto()
    METERS = auto()

    def __str__(self) -> str:
        return self.name.lower()

    @classmethod
    def names(cls) -> List[str]:
        return [str(m) for m in cls]
