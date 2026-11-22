# Network-resilient sensor platform

Raspberry Pi society project. A node keeps taking readings when the Wi-Fi drops, writes them to a local buffer, and uploads them once the link is back.

## Why the buffer exists

School Wi-Fi drops in the middle of a run. If the node only sends live, those samples are gone. Readings go to a file on the Pi first, so a reboot during the outage still keeps what was already sampled.

## Gaps and duplicates

Each reading has:

- a sequence number for that sensor, starting at 1 and stepping by 1
- a reading id that does not change if the same sample is sent again

Sync uploads the next sequence number after the last one the sink has acknowledged. A missing number stops the upload and is reported. It does not skip ahead and leave a quiet hole.

The sink keeps a reading id once. If the response was lost and the node tries again, the second delivery does not create a second row. The local copy stays until that acknowledgement lands.

## Local buffer

`sensor/local_buffer.py` keeps readings in a SQLite file on the machine. That file is gitignored. Putting the same reading id in again does not add a row. A sequence number is unique for a sensor. `pending` returns what is still waiting, oldest sequence first.

## Reconnect

`upload_pending` does nothing while the link is down. When the link is back it walks on from the last acknowledged sequence. A missing number raises `Gap` and leaves the later readings in the file.

`simulate_drop.py` takes two samples, uploads them, drops the link, takes two more, then reconnects. The sink should show sequences 1 through 4, each once.

The sink in this copy is in memory so the script can print the series. A collector on the other end has to treat the reading id the same way and store it once.

## Review

The pipeline was code-reviewed with teammates in the Raspberry Pi society.

## Where it runs

Python 3, on the Pi or on a laptop. A laptop run can force the link down and back up, which is enough to check a drop without a board on the desk.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 simulate_drop.py
python3 -m pytest
```
