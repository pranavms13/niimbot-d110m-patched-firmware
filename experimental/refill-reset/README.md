# Experimental: one Bluetooth command to reset a loaded reel

**Not physically flashed or verified. The published r1 release does not support this command.** This candidate adds NFC counter reset, factory defaults/history clearing, and software reboot to D110_M 4.31. It retains the r1 history-only factory-reset behavior for ordinary command `0x28`.

The intended everyday use is: **leave the replacement reel and its sticker loaded, connect from the Mac, run `reset`, and let the printer restart.** No iPhone NFC scan is needed after this candidate has been installed and physically validated.

## Build and offline checks

From the repository root, with Python 3.10 or newer for the Bluetooth client and Clang capable of compiling for Cortex-M0:

```sh
python3 experimental/refill-reset/build.py
python3 -m venv .venv-refill
. .venv-refill/bin/activate
python -m pip install -r experimental/refill-reset/requirements.txt
python experimental/refill-reset/verify.py
python experimental/refill-reset/verify_client.py
python verification/verify_upload.py --image build/refill-reset/D110_M_V4.31_refill-reset_EXPERIMENTAL.bin
```

Outputs are in `build/refill-reset/`: the headered update file, checksum, manifest, ARM object, and extracted extension. The builder starts with the exact hash-pinned original firmware and adds r1 plus this extension. It does not communicate with the printer. Compiler differences may produce a different candidate hash; test the exact output you intend to install.

See [candidate checksum and completed checks](VALIDATION.md) for the recorded build.

On this Mac, Unicorn's memory mapping crashes inside the execution sandbox; the offline checks ran outside that sandbox. This is an emulator execution requirement, not printer access.

## Bluetooth client

This client never flashes firmware. Installation of the candidate is a separate step using the existing [Bluetooth flashing procedure](../../docs/FLASHING.md), selecting the **experimental** file instead of r1. Software/hardware compatibility remains restricted to the tested base: D110_M, model 2320, firmware 4.31, hardware 4.01. Installing this candidate is a new, unverified firmware change, not a repeat of r1's hardware validation.

After installation, disconnect the NIIMBOT phone app and leave the printer near the Mac:

```sh
# Find the printer's Bluetooth address/UUID.
python experimental/refill-reset/bluetooth_refill.py scan

# Replace ADDRESS with the exact value from scan. This checks patch support.
python experimental/refill-reset/bluetooth_refill.py probe --address ADDRESS

# With the matching replacement reel and sticker loaded, reset once.
python experimental/refill-reset/bluetooth_refill.py reset --address ADDRESS

# Read-only check, also useful after an interrupted connection.
python experimental/refill-reset/bluetooth_refill.py verify --address ADDRESS
```

`reset` checks model/hardware/software and the new capability reply, reads the loaded roll ID, sends the reset once, waits for disconnection, reconnects, and checks the printer-reported count/history. It never automatically resends a reset. If the reply is lost, the outcome is unknown until checked. If software reset leaves the printer powered off, turn it on and run `verify`; that would mean the intended automatic restart has not been established.

## Wire protocol v1

Uses the existing NIIMBOT framing: `55 55 CMD LEN DATA XOR AA AA`. XOR covers `CMD`, `LEN`, and all payload bytes. This is a printer Bluetooth command, **not** a command for NFC Tools.

| Operation | Command | Payload | Reply |
| --- | --- | --- | --- |
| Read-only capability probe | `F0` | `00` | `F1`, payload `52 46 01 10` |
| Combined reset | `F0` | `52 45 46 49 4C 4C 01 A5` followed by the 8-byte expected roll ID | `F1`, payload `52 46 01 STATUS` |

The complete probe packet is `55 55 F0 01 00 F1 AA AA`. Use the **8-byte printer-reported roll ID**, including its cascade byte; a phone's 7-byte NFC UID is not the required representation. The client reads and supplies the correct ID. Wrong IDs and malformed requests do not change the sticker or settings. The magic bytes avoid accidental invocation; they are not authentication or access control.

| Status | Meaning |
| --- | --- |
| `00` | Counter readback and settings write verified; reply constructed before reboot request |
| `01` | Malformed request |
| `02` | Busy printing, moving, or updating |
| `03` | NFC read/authentication failed |
| `04` | Counter or metadata CRC invalid |
| `05` | Wrong/unsupported physical or embedded roll identity |
| `06` | NFC write failed; original counter restored and verified |
| `07` | NFC readback failed; original counter restored and verified |
| `08` | Settings flash save failed; sticker is already zero, flash state is uncertain; no reboot requested |
| `09` | NFC write/readback failed and rollback could not be verified; no settings save/reboot requested |
| `10` | Capability query succeeded; no reset performed |

Only `00` causes software reboot. Successful settings clearing applies to **all remembered rolls** and also restores normal factory settings. Password, tag metadata, label limits, lock/configuration pages, and the reserved counter halfword are preserved.

## Implementation and evidence

- Appended C code uses stock NFC field control (`0x7252`), selection/authentication (`0x533c`), reads (`0x541c`), writes (`0x556a`), TEA (`0x7eb8`, `0x7f18`), CRC (`0xb76c`), and checked settings write (`0xc6f0`). Offsets are relative to the application base `0x01010000`.
- Two additional 4-byte calls change: dispatch at `0x4eee` and response send at `0x4efc`. Unrelated commands fall through to their original dispatcher. The existing r1 patch remains intact. No persistent global RAM is allocated by the extension.
- The command authenticates and checks the expected physical ID, decrypts and validates the 120-byte record locally, checks its embedded ID, then reauthenticates the same ID before writing. Only pages 5 and 6 are changed. It verifies ciphertext readback before saving settings. Failure recovery authenticates the same ID before attempting to restore the original counter.
- New settings are prepared locally. The original settings writer performs erase/program/readback with retries. Only after successful persistence are the RAM history and pending usage cleared.
- The post-send hook uses the original transport, waits 500 ms with interrupts active while feeding the watchdog, then enables `MRSTGEN.RST_EN.SOFT` at `0x000f8574` and writes `0x55` to `MRSTGEN.RESET` at `0x000f857c`. These registers and key come from the [YiCHiP YC3122 SDK device header](https://github.com/RT-Thread/rt-thread/blob/master/bsp/yichip/yc3122-pos/libraries/CMSIS/Device/YICHIP/YC3122/Include/yc3122.h). Firmware watchdog code independently matches the SDK's reset-enable register location. Radio acknowledgement delivery and the board's power behavior remain physical-test questions.
- `verify.py` runs the compiled ARM instructions and original command wrapper, crypto, CRC, memory operations and checked flash-writer control flow in Unicorn. NFC, flash peripherals, allocation, clock, response transport and reset effects are simulated. Twelve test groups cover success, preserved fields, malformed commands, busy states, identity swaps, CRCs, write/readback failure recovery, flash failure, and ordinary r1 reset behavior.
- The stock upload receiver simulation accepted **589 chunks**, staged the entire candidate, and returned its checksum-success reply. It does not execute the bootloader or establish successful boot.

## Physical validation still required

Install the candidate with the roll removed, reconnect, and first run the capability probe. Load the replacement reel, record its current count, then run the combined reset once. Confirm that it restarts without pressing the power button, the same roll reports zero, and history contains no old rolls (the active zero-count roll may be reinserted as one history record). Power-cycle once more to check persistence, then print one label and confirm the count advances to one.

The two NFC page writes and the separate settings flash write cannot be atomic together. Removing the sticker or cutting power mid-operation can leave a partial counter or settings write; simulated rollback tests do not guarantee recovery from power loss. This candidate has **no physical success claim**, and does not replace the verified r1 release until the new sequence has been tested on the printer.
