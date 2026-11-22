"""SQLite file of readings that are still waiting for an acknowledgement."""

import sqlite3
from pathlib import Path

from sensor.reading import Reading


class DuplicateSequence(Exception):
    """This sensor already stored that sequence under a different id."""


class LocalBuffer:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS readings (
                reading_id TEXT PRIMARY KEY,
                sensor_id TEXT NOT NULL,
                seq INTEGER NOT NULL,
                value REAL NOT NULL,
                recorded_at TEXT NOT NULL,
                acked INTEGER NOT NULL DEFAULT 0,
                UNIQUE (sensor_id, seq)
            )
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def append(self, reading: Reading) -> bool:
        """Store a reading.

        False means this reading id is already in the file, so a retry
        did not add a second row. The same sequence with a new id raises.
        """
        found = self._conn.execute(
            "SELECT reading_id FROM readings WHERE reading_id = ?",
            (reading.reading_id,),
        ).fetchone()
        if found is not None:
            return False

        clash = self._conn.execute(
            """
            SELECT reading_id FROM readings
            WHERE sensor_id = ? AND seq = ?
            """,
            (reading.sensor_id, reading.seq),
        ).fetchone()
        if clash is not None:
            raise DuplicateSequence(
                f"{reading.sensor_id} already has sequence {reading.seq}"
            )

        self._conn.execute(
            """
            INSERT INTO readings
                (reading_id, sensor_id, seq, value, recorded_at, acked)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (
                reading.reading_id,
                reading.sensor_id,
                reading.seq,
                reading.value,
                reading.recorded_at,
            ),
        )
        self._conn.commit()
        return True

    def pending(self, sensor_id: str) -> list[Reading]:
        rows = self._conn.execute(
            """
            SELECT reading_id, sensor_id, seq, value, recorded_at
            FROM readings
            WHERE sensor_id = ? AND acked = 0
            ORDER BY seq
            """,
            (sensor_id,),
        ).fetchall()
        return [_row_to_reading(row) for row in rows]

    def last_acked_seq(self, sensor_id: str) -> int:
        row = self._conn.execute(
            """
            SELECT MAX(seq) AS seq FROM readings
            WHERE sensor_id = ? AND acked = 1
            """,
            (sensor_id,),
        ).fetchone()
        if row is None or row["seq"] is None:
            return 0
        return int(row["seq"])

    def mark_acked(self, reading_id: str) -> None:
        cursor = self._conn.execute(
            "UPDATE readings SET acked = 1 WHERE reading_id = ?",
            (reading_id,),
        )
        if cursor.rowcount != 1:
            raise KeyError(reading_id)
        self._conn.commit()


def _row_to_reading(row: sqlite3.Row) -> Reading:
    return Reading(
        sensor_id=row["sensor_id"],
        seq=int(row["seq"]),
        reading_id=row["reading_id"],
        value=float(row["value"]),
        recorded_at=row["recorded_at"],
    )
