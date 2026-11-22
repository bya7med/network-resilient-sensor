"""Send pending readings once the link is up, in sequence order."""

from sensor.link import Link
from sensor.local_buffer import LocalBuffer
from sensor.sink import Sink


class Gap(Exception):
    """The next sequence number is missing, so upload stops."""

    def __init__(self, sensor_id: str, expected: int, found: int) -> None:
        self.sensor_id = sensor_id
        self.expected = expected
        self.found = found
        super().__init__(
            f"{sensor_id}: expected sequence {expected}, found {found}"
        )


def upload_pending(
    buffer: LocalBuffer,
    sink: Sink,
    link: Link,
    sensor_id: str,
) -> int:
    """Upload what is still waiting.

    Link down: leave the buffer alone and return 0.
    A hole in the sequence raises Gap. Readings after the hole stay on disk.
    The local row is marked acknowledged only after the sink has accepted it.
    """
    if not link.is_up():
        return 0

    expected = buffer.last_acked_seq(sensor_id) + 1
    sent = 0
    for reading in buffer.pending(sensor_id):
        if reading.seq != expected:
            raise Gap(sensor_id, expected, reading.seq)
        sink.accept(reading)
        buffer.mark_acked(reading.reading_id)
        expected += 1
        sent += 1
    return sent
