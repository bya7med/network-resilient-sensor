"""Where an uploaded reading lands.

The same reading id is stored once. A retry after a lost response must not
grow the series.
"""

from sensor.reading import Reading


class Sink:
    def __init__(self) -> None:
        self._by_id: dict[str, Reading] = {}
        self._order: list[str] = []

    def accept(self, reading: Reading) -> bool:
        """True the first time this id is stored, False on a repeat."""
        if reading.reading_id in self._by_id:
            return False
        self._by_id[reading.reading_id] = reading
        self._order.append(reading.reading_id)
        return True

    def series(self, sensor_id: str) -> list[Reading]:
        return [
            self._by_id[reading_id]
            for reading_id in self._order
            if self._by_id[reading_id].sensor_id == sensor_id
        ]
