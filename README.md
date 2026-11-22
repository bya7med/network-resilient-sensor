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

## Review

The pipeline was code-reviewed with teammates in the Raspberry Pi society.

## Where it runs

Python 3, on the Pi or on a laptop. A laptop run can force the link down and back up, which is enough to check a drop without a board on the desk.
