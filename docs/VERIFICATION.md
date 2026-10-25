# Verification

## Physical test — 26 October 2026

One D110_M with hardware **4.01** and base firmware **4.31** was tested. The patched file's SHA-256 was `909fe39cf7176e54999fb5a113f94c6792d503b9578362a1a79e00200564ecc8`.

| Check | Observed result |
| --- | --- |
| Bluetooth firmware upload | All 583 chunks transferred |
| Printer's payload check | Success |
| Update commit | Success confirmed by printer |
| Boot/connect after update | Successful after owner turned printer on |
| History before update | One roll record, seven used labels |
| History after update, before reset | Same record and count retained |
| Patched factory reset | Success acknowledgement; zero history records |
| Owner-confirmed power cycle with roll removed | Fresh Bluetooth query still returned zero records |
| Reset sticker loaded on replacement reel | Printer RFID information and history both reported zero used |
| One-label print | One page complete; print/feed progress both 100% |
| Count after print | Printer RFID information and history both reported one used |
| Physical output | Owner confirmed a clear “REFILL TEST” label |

The NFC reset also produced two write acknowledgements and read back the expected zero-counter ciphertext before the reel was inserted.

The initial print-script setup attempt stopped before sending raster data because it expected a one-byte page-size acknowledgement. The firmware returns `01 00` on success. After correcting that check, the test again verified zero usage before sending and completing one label. No second printed test label was requested.

The [anonymized hardware result](../verification/hardware-result.json) records these observations. Device addresses, roll identities, serial numbers, and raw logs are not published.

## Offline checks

- [Original firmware checks](../verification/verify_firmware.py): startup decompression/key extraction; 100 deterministic TEA/CRC vectors; maximum-count restoration; stock reset preserving history; all 256 history-query selectors; startup CRC recovery; ring eviction.
- [Patch checks](../verification/verify_patch.py): deterministic build, exact changed bytes, independently decoded Thumb instructions, 12 varied settings records, history-only clearing, normal defaults and response preservation, stack/register preservation, saved CRC and simulated reload, and zero-count lookup after reset.
- [Upload checks](../verification/verify_upload.py): all 583 chunks plus finish/check execute through the stock receiver using virtual staging flash; the staged application matches the published payload; equal-version 4.31 is accepted; damaged header CRC is rejected.

The [saved reports](../verification/reports/) can be reproduced using the commands in [TECHNICAL.md](TECHNICAL.md).

## Limits

- These results establish behavior on **one physical printer and one tested sticker/replacement reel**, not every D110_M revision or third-party roll.
- A full application-flash readback was not performed. Successful update replies, boot, changed reset behavior, persistence and a physical print supplied the hardware evidence.
- The sticker's memory was not independently reread after printing; the final usage came from the printer's RFID-information and history responses.
- Offline tests substitute radio/peripheral/flash I/O as documented. They do not emulate the commit worker or separate bootloader.
- Stock rollback and recovery from an unbootable printer were not physically tested.
