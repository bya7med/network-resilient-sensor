"""Record samples, drop the link, then upload what was held back.

Run from the repo root:

    python3 simulate_drop.py
"""

import tempfile
from pathlib import Path

from sensor.link import Link
from sensor.local_buffer import LocalBuffer
from sensor.reading import Reading
from sensor.sink import Sink
from sensor.sync import upload_pending


SENSOR = "temp-1"


def sample(seq: int, value: float) -> Reading:
    return Reading(
        sensor_id=SENSOR,
        seq=seq,
        reading_id=f"{SENSOR}-{seq}",
        value=value,
        recorded_at=f"2026-11-22T15:{seq:02d}:00Z",
    )


def main() -> None:
    directory = tempfile.mkdtemp(prefix="sensor-buffer-")
    buffer = LocalBuffer(Path(directory) / "readings.sqlite")
    link = Link(up=True)
    sink = Sink()

    buffer.append(sample(1, 18.2))
    buffer.append(sample(2, 18.4))
    upload_pending(buffer, sink, link, SENSOR)

    link.drop()
    buffer.append(sample(3, 18.1))
    buffer.append(sample(4, 17.9))
    sent_while_down = upload_pending(buffer, sink, link, SENSOR)
    held = [item.seq for item in buffer.pending(SENSOR)]
    print(f"link down, uploaded {sent_while_down}, still on disk {held}")

    link.reconnect()
    sent = upload_pending(buffer, sink, link, SENSOR)
    series = [(item.seq, item.value) for item in sink.series(SENSOR)]
    print(f"link back, uploaded {sent}")
    print(f"sink series {series}")
    buffer.close()


if __name__ == "__main__":
    main()
