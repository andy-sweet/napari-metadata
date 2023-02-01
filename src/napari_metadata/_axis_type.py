from enum import Enum, auto
from typing import List


class AxisType(Enum):
    """Supported axis types."""

    SPACE = auto()
    TIME = auto()
    CHANNEL = auto()

    def __str__(self) -> str:
        return self.name.lower()

    @classmethod
    def names(cls) -> List[str]:
        return [str(m) for m in cls]
