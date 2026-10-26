# Experimental candidate validation

**2026-10-26: automatic restart is confirmed with USB power connected. Battery-only restart remains unresolved.** Testing used one D110_M, model 2320, hardware 4.01, firmware base 4.31.

## Current build

Built with Apple Clang 21.0.0 (`clang-2100.3.34.2`):

- File: `D110_M_V4.31_refill-reset_EXPERIMENTAL.bin`
- SHA-256: `c320111084d1199d6947e704212a7d8b98d14171cd4352931b0ada90e7a40635`
- Size: 117,976 bytes including the 28-byte update header
- Extension: 1,412 bytes appended after the r1 extension
- C source SHA-256: `af42ec31f4cb25bac94f35c8c7bae393ea5b6f0c13dd529642e88ada355a1b8f`

This is the backup-register marker plus ARM `SYSRESETREQ` build. It was restored after the unsuccessful battery-only experiment; rebuilding reproduced the exact tested hash. No bootloader changes or diagnostic memory-read commands are included. The published r1 release is unchanged.

## Physical observations

| Check | Result |
| --- | --- |
| Bluetooth installation and restoration | 590 chunks; device checksum verification and commit succeeded |
| USB-powered reset | Success acknowledgement, Bluetooth disconnect and reconnection about 8.1 seconds later; owner confirmed no power-button press |
| Count/history after USB restart | Same reel at 0 used; its sole saved history record also at 0 |
| Printing after USB restart | After unplugging USB, one test print completed; reel and history both changed 0→1 |
| Battery-only reset | Acknowledged, but no automatic reconnection within the client timeout |
| Final restored-build retest | Pending loaded-reel check |

The first USB restart test started at zero. Earlier builds had established 1→0 reset and persistence after manual power cycling; the final restored-build retest will check that transition with automatic restart. The client cannot independently distinguish a human power-button press from automatic startup, so its `automatic_restart_verified: false` output means it has not verified that fact itself. The owner confirmation above is separate evidence.

One current reel can be reinserted into history during detection, so one zero-count record after reset is expected. Multiple different saved rolls were cleared in offline tests, not on hardware. Factory-default fields were compared against the stock reset path offline; individual settings were not all queried physically. Physical power-loss recovery during NFC/flash writes has not been established.

## Offline checks

The current image passed **17 ARM test groups**, **4 update-receiver checks**, and **4 Bluetooth client checks**. The existing r1 suite had previously passed 21 checks.

The ARM tests execute the compiled extension plus stock command handling, crypto, CRC, memory operations, flash-writer control flow, power-on handler and periodic shutdown worker. They cover success, preserved fields, busy/malformed requests, tag swaps, CRC failure, write/readback rollback, flash failure, ordinary r1 reset, valid/invalid/consumed startup cookies, and failed backup-register writes. NFC, flash peripherals, allocation, clocks, transport, reset effects and backup-register retention are simulated. Full ROM boot and physical power continuity are not emulated. The upload simulation stages all 590 chunks and validates the image but does not execute the bootloader.

## Earlier experiments

| Image SHA-256 | Outcome |
| --- | --- |
| `9b831e773e1933175fd5108782ae71ad826afb950c6557a295f1c6691b190861` | Initial extension flashed and printed; reset returned NFC error `03`, leaving count 1. Corrected by cycling the RF field before every reselection. |
| `f21f58e55c74b79f00c0cfbf5c75c0b24c8b31e74b50928c9a3223da8593e883` | NFC reset 1→0 and persistence after manual power cycling passed. Chip reset required manual power-on. |
| `e674a75ad0d03ba6f617a90aa2f458ff0749ea53d51500675cc6eb1996eaf616` | Added a startup hook gated on `RST_TYPE.SOFT`; still needed manual power-on. Count/history verified at zero afterward. |
| `8b76ff8c7a4384004895ebe56ad65761a2d59a0a52e7fc196bf23f8cf9c00b0e` | Used ARM system reset with a reset-status-bit marker. No automatic reconnection on battery or USB power. |
| `29c99c8a051f26b3b1e1c8a00eebf7151c84316dd49b8155b2cf4b89bd75f051` | Backup marker plus IC-reset key `0x50`, with GPIO reset disabled. No battery-only automatic reconnection; a later read still showed history count 1 despite the earlier acknowledgement. Reverted to the USB-working build. |

A private diagnostic build read the reset registers and fixed 64 KiB bootloader region. After manual power-on, `RST_EN=2` and `RST_TYPE=0`; the startup hook had already cleared SOFT, so that reading does not establish its initial value. The recovered bootloader uses ARM `SYSRESETREQ` at `0x0100111c–0x01001126`. Both supplied firmware files contained the application only, one with an update header. The bootloader was read, never modified; raw bootloader and device logs remain local.

The backup-register marker fixes startup on USB power, but the precise battery-only failure mechanism has not been established. Do not infer that GPIO preservation or another reset key is a verified battery solution. Use the documented USB-powered procedure for automatic restart.
