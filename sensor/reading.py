"""One sample, with the id it will keep if it has to be sent again."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Reading:
    sensor_id: str
    seq: int
    reading_id: str
    value: float
    recorded_at: str

    def __post_init__(self) -> None:
        if not self.sensor_id:
            raise ValueError("sensor_id is required")
        if not self.reading_id:
            raise ValueError("reading_id is required")
        if self.seq < 1:
            raise ValueError("sequence numbers start at 1")
