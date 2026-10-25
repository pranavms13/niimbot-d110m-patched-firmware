# Install the patched firmware

Flashing modified firmware can leave a printer unable to boot. This image was physically tested on **one D110_M, hardware 4.01, running firmware 4.31**. No hardware recovery procedure was validated. The included stock update file is not a backup of your printer's bootloader, calibration, or settings.

If the patch is already installed, use [the reset steps](RESET.md). Do not reflash for every refill.

## Check compatibility and the download

| Item | Tested value |
| --- | --- |
| Model | **D110_M** |
| Model ID | `2320` / `0x0910` |
| Hardware | **4.01** |
| Base firmware | **4.31** |
| Firmware file | `D110_M_V4.31_history-reset.bin` |
| Version to enter in flasher | **4.31** |

**Do not use this image on D110, another model, or an unverified hardware/firmware family.** On this tested model, version response bytes `04 1F` mean firmware **4.31**, and `04 01` mean hardware **4.01**. NiimBlue may display both possible interpretations as `4.31/10.55` and `4.01/10.25`.

Download the [patched update file](../firmware/D110_M_V4.31_history-reset.bin) using GitHub's **Download raw file** button, or use the direct download in the [README](../README.md). Do not save the GitHub HTML page as a `.bin` file.

On macOS, check the file:

```bash
shasum -a 256 D110_M_V4.31_history-reset.bin
```

Expected:

```text
909fe39cf7176e54999fb5a113f94c6792d503b9578362a1a79e00200564ecc8
```

The complete update file is **116,564 bytes**, including its 28-byte header. A raw `*_app.bin` payload is not interchangeable with this update file.

## Flash over Bluetooth on a Mac

1. **Remove the roll and NFC sticker.** Finish or cancel printing. Disconnect the iPhone NIIMBOT app and any other printer client.
2. Charge the printer, turn it on, and keep it near the Mac. Prevent the Mac from sleeping during the update.
3. Open [NiimBlue](https://niim.blue) in **Google Chrome on the Mac**.
4. Choose **Bluetooth → Connect**, then select your D110_M. Grant Chrome Bluetooth permission in macOS if requested.
5. Open the connected printer's **gear menu → Firmware flashing**.
6. Browse to **`D110_M_V4.31_history-reset.bin`**. Confirm the version field says **4.31**.
7. Click **Burn** and accept NiimBlue's confirmation if you decide to install it.
8. Keep the printer powered and the tab in the foreground. Wait for the **entire update**, including checksum checking and commit after all upload chunks. Do not interrupt it when the counter reaches the last chunk.
9. Wait for the completion result. The printer may briefly stop responding. In the physical test, it needed to be turned on again before it advertised over Bluetooth. Once the update has completed, turn it on if needed and reconnect.

The verified upload used **583 chunks** and the NiimBlue library's packet format. The physical test was performed with a direct Bluetooth client, not by clicking through the NiimBlue UI. The UI route above follows the [NiimBlue author's instructions](https://github.com/MultiMote/niimblue/wiki/Flashing-firmwares) and its [firmware updater source](https://github.com/MultiMote/niimblue/blob/main/src/components/basic/FirmwareUpdater.svelte).

Chrome on iPhone does not support website-to-Bluetooth connections; use the Mac for this route. NFC Tools/CENFC interact with the sticker and cannot install printer firmware. See [Chrome's Bluetooth guidance](https://support.google.com/chrome/answer/6362090).

## Verify the patch

1. Keep the roll removed and reconnect.
2. Choose **gear → Tests → Reset**, then wait for completion.
3. Power the printer off and on with the roll still removed.
4. Follow [RESET.md](RESET.md) to reset the sticker and load the replacement roll.
5. Refresh roll information. It should show zero used. Print one test label and confirm it shows one used and produces a readable label.

The displayed firmware version remains **4.31**. This is intentional; the behavior of factory reset is the relevant verification.

## Rejection or failed update

Retain the exact error and the stage where it occurred. Do not substitute another model's image or repeatedly retry while the printer might still be updating.

Some D110_M revisions are reported to reject equal-version updates. The supplied 4.31 receiver accepted equal version 4.31 both in offline execution and in the physical test, so this release does not increase the version. See [the community's version-restriction notes](https://printers.niim.blue/firmware/flashing-firmware/). An unexplained rejection on another unit needs investigation rather than a blind version change.

## Return to stock behavior

If the printer still boots and its updater remains reachable, the same procedure can be attempted with [the original 4.31 image](../firmware/D110_M_V4.31_original.bin), using version **4.31**. Stock factory reset will again preserve roll history.

Stock restoration was **not physically tested**. Neither this file nor Bluetooth alone guarantees recovery from an unbootable device. No programmer pinout or bootloader recovery procedure is provided.
