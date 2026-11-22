"""The file on disk keeps order and does not store the same id twice."""

from pathlib import Path

import pytest

from sensor.local_buffer import DuplicateSequence, LocalBuffer
from sensor.reading import Reading


def reading(seq: int, reading_id: str | None = None, value: float = 20.0) -> Reading:
    return Reading(
        sensor_id="bench",
        seq=seq,
        reading_id=reading_id or f"bench-{seq}",
        value=value,
        recorded_at="2026-11-22T12:00:00Z",
    )


def test_pending_comes_back_in_sequence_order(tmp_path: Path) -> None:
    buffer = LocalBuffer(tmp_path / "readings.sqlite")
    buffer.append(reading(2, value=2.0))
    buffer.append(reading(1, value=1.0))
    assert [item.seq for item in buffer.pending("bench")] == [1, 2]
    buffer.close()


def test_same_reading_id_is_stored_once(tmp_path: Path) -> None:
    buffer = LocalBuffer(tmp_path / "readings.sqlite")
    assert buffer.append(reading(1)) is True
    assert buffer.append(reading(1)) is False
    assert len(buffer.pending("bench")) == 1
    buffer.close()


def test_same_sequence_with_a_new_id_is_rejected(tmp_path: Path) -> None:
    buffer = LocalBuffer(tmp_path / "readings.sqlite")
    buffer.append(reading(1, reading_id="a"))
    with pytest.raises(DuplicateSequence):
        buffer.append(reading(1, reading_id="b"))
    buffer.close()


def test_buffer_is_still_there_after_reopen(tmp_path: Path) -> None:
    path = tmp_path / "readings.sqlite"
    buffer = LocalBuffer(path)
    buffer.append(reading(1, value=18.2))
    buffer.close()

    again = LocalBuffer(path)
    pending = again.pending("bench")
    assert [item.reading_id for item in pending] == ["bench-1"]
    assert pending[0].value == 18.2
    again.close()


def test_acknowledged_readings_drop_out_of_pending(tmp_path: Path) -> None:
    buffer = LocalBuffer(tmp_path / "readings.sqlite")
    buffer.append(reading(1))
    buffer.append(reading(2))
    buffer.mark_acked("bench-1")
    assert [item.seq for item in buffer.pending("bench")] == [2]
    assert buffer.last_acked_seq("bench") == 1
    buffer.close()
