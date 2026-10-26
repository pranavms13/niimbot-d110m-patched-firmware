# Experimental candidate validation

Status: built and checked offline; **not physically installed or tested**.

The candidate produced with Apple Clang 21.0.0 (`clang-2100.3.34.2`):

- File: `D110_M_V4.31_refill-reset_EXPERIMENTAL.bin`
- Size: 117,776 bytes, including the 28-byte update header
- SHA-256: `9b831e773e1933175fd5108782ae71ad826afb950c6557a295f1c6691b190861`
- Extension: 1,212 bytes appended after the existing r1 extension
- C source SHA-256: `8d50a32f3f35d900fab76676f7003e6f52c633600f1f9dff97933caee779d902`

Checks completed:

| Check | Result |
| --- | --- |
| Compiled ARM extension and original command wrapper | 12 groups passed, including failure handling and ordinary reset regression |
| Bluetooth framing, fragmented replies/writes, RFID parsing | 4 groups passed without Bluetooth hardware |
| Original firmware update receiver with this candidate | 589 chunks accepted; final checksum verified; version and malformed-header cases passed |
| Existing r1 verification suite | All 21 checks passed, including the unchanged default upload test |

The ARM tests execute stock crypto, CRC, memory routines and flash-writer control flow. NFC operations, flash peripherals, transport, allocation, clock and reset effects are simulated. An observed reset-register write establishes the intended instruction sequence, not a physical restart. The upload simulation does not execute the bootloader.

Run the commands in [README.md](README.md) against any rebuilt image. Compiler changes can change the binary and checksum. Physical validation must establish NFC write/readback, reply delivery, automatic restart, persistence and printing before this replaces the tested r1 release.
