from enum import Enum, auto
from typing import List


class TimeUnits(Enum):
    NONE = auto()
    NANOSECONDS = auto()
    MICROSECONDS = auto()
    MILLISECONDS = auto()
    SECONDS = auto()

    def __str__(self) -> str:
        return self.name.lower()

    @classmethod
    def names(cls) -> List[str]:
        return [str(m) for m in cls]
