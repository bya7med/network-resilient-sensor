"""Wi-Fi drop, reconnect, a repeated upload, and a hole in the sequence."""

from pathlib import Path

import pytest

from sensor.link import Link
from sensor.local_buffer import LocalBuffer
from sensor.reading import Reading
from sensor.sink import Sink
from sensor.sync import Gap, upload_pending


def reading(seq: int, value: float = 20.0) -> Reading:
    return Reading(
        sensor_id="bench",
        seq=seq,
        reading_id=f"bench-{seq}",
        value=value,
        recorded_at="2026-11-22T12:00:00Z",
    )


def test_drop_keeps_readings_until_reconnect(tmp_path: Path) -> None:
    buffer = LocalBuffer(tmp_path / "readings.sqlite")
    link = Link(up=True)
    sink = Sink()

    buffer.append(reading(1, 18.0))
    assert upload_pending(buffer, sink, link, "bench") == 1

    link.drop()
    buffer.append(reading(2, 18.5))
    buffer.append(reading(3, 19.0))
    assert upload_pending(buffer, sink, link, "bench") == 0
    assert [item.seq for item in sink.series("bench")] == [1]
    assert [item.seq for item in buffer.pending("bench")] == [2, 3]

    link.reconnect()
    assert upload_pending(buffer, sink, link, "bench") == 2
    assert [item.seq for item in sink.series("bench")] == [1, 2, 3]
    assert buffer.pending("bench") == []

    assert upload_pending(buffer, sink, link, "bench") == 0
    assert [item.seq for item in sink.series("bench")] == [1, 2, 3]
    buffer.close()


def test_repeat_delivery_of_the_same_id_is_one_row(tmp_path: Path) -> None:
    buffer = LocalBuffer(tmp_path / "readings.sqlite")
    link = Link(up=True)
    sink = Sink()
    sample = reading(1, 21.5)

    buffer.append(sample)
    assert sink.accept(sample) is True
    assert sink.accept(sample) is False

    assert upload_pending(buffer, sink, link, "bench") == 1
    assert len(sink.series("bench")) == 1
    assert buffer.pending("bench") == []
    buffer.close()


def test_missing_sequence_stops_the_upload(tmp_path: Path) -> None:
    buffer = LocalBuffer(tmp_path / "readings.sqlite")
    link = Link(up=True)
    sink = Sink()
    buffer.append(reading(1, 18.0))
    buffer.append(reading(3, 19.0))

    with pytest.raises(Gap) as raised:
        upload_pending(buffer, sink, link, "bench")

    assert raised.value.expected == 2
    assert raised.value.found == 3
    assert [item.seq for item in sink.series("bench")] == [1]
    assert [item.seq for item in buffer.pending("bench")] == [3]
    buffer.close()


def test_does_not_start_from_the_middle_of_a_series(tmp_path: Path) -> None:
    buffer = LocalBuffer(tmp_path / "readings.sqlite")
    link = Link(up=True)
    sink = Sink()
    buffer.append(reading(3, 19.0))

    with pytest.raises(Gap) as raised:
        upload_pending(buffer, sink, link, "bench")

    assert raised.value.expected == 1
    assert raised.value.found == 3
    assert sink.series("bench") == []
    assert [item.seq for item in buffer.pending("bench")] == [3]
    buffer.close()
