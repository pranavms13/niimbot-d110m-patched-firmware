# Experimental candidate validation

**2026-10-26 hardware result: reset and persistence passed; automatic restart failed.** Tested on one D110_M, model 2320, hardware 4.01, firmware base 4.31. The printer is left running this corrected experimental image, with its loaded reel at zero used.

## Exact installed build

Built with Apple Clang 21.0.0 (`clang-2100.3.34.2`):

- File: `D110_M_V4.31_refill-reset_EXPERIMENTAL.bin`
- Size: 117,848 bytes, including the 28-byte update header
- SHA-256: `f21f58e55c74b79f00c0cfbf5c75c0b24c8b31e74b50928c9a3223da8593e883`
- Extension: 1,284 bytes appended after the existing r1 extension
- Current C source SHA-256: `0e127a3a44d42dad481fca6f37307610857c8e9d978ad0a9026bfe1aea572703`

The source header comment was updated after testing. Rebuilding produced the identical firmware hash above.

## Physical observations

| Check | Result |
| --- | --- |
| Bluetooth update | 590 chunks; device checksum verification and commit both succeeded |
| Boot and read-only capability query | Passed after turning the printer on following the update |
| Before reset | One completed test print established 1 used, also stored in the sole history record |
| Combined reset | Success reply `55 55 F1 04 52 46 01 00 E0 AA AA`; command verifies NFC ciphertext and settings flash readback before this reply |
| Reconnection | Bluetooth disconnected; owner pressed power to turn the printer back on |
| Count/history after restart | Same reel reported 0 used; history contained only that reel at 0 |
| Further manual power cycle | Same reel and history still reported 0 |
| Automatic restart | **Failed. Owner explicitly confirmed a power-button press was necessary** |

The loaded reel can be reinserted into history during detection. One current record at zero is therefore expected after startup; the earlier used count did not return. This physical test had only one stored roll. Clearing a history containing multiple different rolls was checked offline, not on hardware. Printing after the combined reset was not tested in this session. Factory-default fields were compared with the stock reset path offline; each setting was not queried on hardware.

The earlier candidate (`9b831e773e1933175fd5108782ae71ad826afb950c6557a295f1c6691b190861`) flashed and printed, but its reset returned NFC error `03` and left the count at 1. The correction cycles the RF field before every selection/authentication, including reselection before writing and rollback. The initial simulation omitted that tag-state requirement; the revised model rejects reselection without a fresh field state.

## Offline checks

The corrected candidate passed all 12 ARM test groups and all 4 update-receiver checks, including 590-chunk staging and final checksum validation. The Bluetooth framing/parser checks also passed (4 groups). The existing r1 suite passed all 21 checks before this NFC-only correction.

The ARM tests execute stock crypto, CRC, memory routines and flash-writer control flow. NFC operations, flash peripherals, transport, allocation, clock and reset effects are simulated. A reset-register write does not establish automatic boot; the physical test demonstrates this limitation. The upload simulation does not execute the bootloader.

Run the commands in [README.md](README.md) against rebuilt images. Compiler changes can change the binary and checksum. This candidate remains experimental, with automatic restart still requiring a fix and physical retest; it does not replace the published r1 release. Raw logs containing device identifiers are retained locally rather than published.
