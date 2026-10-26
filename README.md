# NIIMBOT D110_M: refill reset firmware

Firmware modifications for **D110_M 4.31, hardware 4.01**, to reuse an NFC sticker with a replacement reel of the same label size and type. Two versions are available:

| Version | Reset method | Hardware result |
| --- | --- | --- |
| Published **r1 release** | Clear printer history, then reset the sticker with an iPhone | Reset, persistence and a replacement-reel test print passed |
| **Experimental Bluetooth reset** | One Mac command resets the loaded sticker and printer history | Count reset and persistence passed; **automatic restart works with USB power connected** |

**Connect USB power before using automatic restart.** The latest experimental build reconnects automatically when USB-powered. Battery-only restart remains unresolved; on battery, a manual power-on may be needed. Both versions have been tested on only one D110_M. See the [r1 results](docs/VERIFICATION.md) and [experimental hardware results](https://github.com/pranavms13/niimbot-d110m-patched-firmware/blob/feature/bluetooth-refill-reset/experimental/refill-reset/VALIDATION.md).

This is an unofficial firmware modification. A failed update or incompatible image can leave a printer unable to boot. Compatibility with other models or hardware versions has not been established, and Bluetooth recovery is not guaranteed.

## Quick reset: experimental Bluetooth firmware

**Use this procedure only if the corrected experimental firmware is already installed.** The r1 release downloads below do not support this command. You do not need to flash again for each refill, and no iPhone NFC write is needed for this procedure.

For first-time Mac client setup, use Python 3.10 or newer:

```sh
git clone --branch feature/bluetooth-refill-reset https://github.com/pranavms13/niimbot-d110m-patched-firmware.git
cd niimbot-d110m-patched-firmware
python3 -m venv .venv-refill
. .venv-refill/bin/activate
python -m pip install bleak==3.0.2
```

If you already have a clone, update its `feature/bluetooth-refill-reset` branch instead of cloning again. For each refill:

1. Connect the printer to **USB power** (a charger is sufficient; commands still use Bluetooth). Leave the replacement reel and its NFC sticker **loaded**, close the lid, turn the printer on near the Mac, and disconnect the NIIMBOT phone app.
2. In the repository folder, activate the environment and find the printer:

   ```sh
   . .venv-refill/bin/activate
   python experimental/refill-reset/bluetooth_refill.py scan
   ```

3. Replace `ADDRESS` with the address/UUID shown by the scan, then run:

   ```sh
   python experimental/refill-reset/bluetooth_refill.py reset --address ADDRESS
   ```

4. Wait for **“NFC and settings writes acknowledged.”** Keep USB power connected and **leave the power button untouched**. The printer should restart automatically; the client reconnects and checks that the same reel reports `used: 0`. It allows about a minute for reconnection.
5. If reconnection times out, turn the printer on and run this read-only check:

   ```sh
   python experimental/refill-reset/bluetooth_refill.py verify --address ADDRESS
   ```

The command clears all remembered rolls and restores factory settings. The loaded reel may immediately appear again as **one history record at zero**; this is expected. If an error occurs or the reply is lost, inspect the result before sending another reset.

Reset, persistence and printing after a combined reset have been checked on one printer. The owner confirmed automatic restart without a power-button press with USB connected. Battery-only automatic restart failed. The client reports `automatic_restart_verified: false` because it cannot independently detect a human button press; this field does not override the separately recorded hardware observations. See the [experimental build/install instructions and limitations](https://github.com/pranavms13/niimbot-d110m-patched-firmware/blob/feature/bluetooth-refill-reset/experimental/refill-reset/README.md).

## Quick reset: published r1 firmware and iPhone

**Use this procedure for the published r1 firmware.** It requires two separate resets. The firmware must already be installed; you do not need to flash it again.

1. Remove the reel and its NFC sticker. Disconnect the NIIMBOT phone app.
2. Turn the printer **on**. On the Mac, open [NiimBlue](https://niim.blue) in **Google Chrome**, connect by Bluetooth, and select **gear → Tests → Reset**. Wait for it to finish. This clears all remembered rolls and restores factory settings.
3. Turn the printer **off**. On the iPhone, open **NFC Tools → Other → Advanced NFC commands**.
4. For the sticker verified in this project, paste this batch and hold the sticker at the top of the phone until it finishes:

   ```text
   1B:12:34:56:78,A2:05:74:2F:C7:63,A2:06:E0:17:DB:F9,30:05
   ```

   Expect `55 55`, then `0A`, then `0A`, and a readback starting with `74 2F C7 63 E0 17 DB F9`. If authentication or a write fails, stop. **For a different sticker, [validate it first](docs/RESET.md#read-or-validate-another-sticker-before-writing); this batch is not universal.**
5. Attach the sticker to a replacement reel matching the original label size/type, load it, and turn the printer **on**. Reconnect and refresh the roll information: it should show **0 used**, then **1 used** after printing one label.

See the [full reset guide and troubleshooting](docs/RESET.md) if a response differs or the old count remains.

## Start here

| What you need | Instructions |
| --- | --- |
| Reset with experimental firmware already installed | [Bluetooth reset steps](#quick-reset-experimental-bluetooth-firmware) |
| Reset with published r1 firmware already installed | [Printer and iPhone NFC steps](#quick-reset-published-r1-firmware-and-iphone) |
| Install the patch for the first time | [Flash over Bluetooth from a Mac](docs/FLASHING.md) |
| Understand the change or rebuild it | [Technical details and reproducible build](docs/TECHNICAL.md) |
| See what was actually tested | [Verification](docs/VERIFICATION.md) |

## Downloads: published r1 release

**These downloads contain the history-only r1 patch, not the experimental Bluetooth command.** For the experimental image, use its [build and installation guide](https://github.com/pranavms13/niimbot-d110m-patched-firmware/blob/feature/bluetooth-refill-reset/experimental/refill-reset/README.md).

- **[Download patched D110_M 4.31 firmware](https://github.com/pranavms13/niimbot-d110m-patched-firmware/releases/download/v4.31-history-reset-r1/D110_M_V4.31_history-reset.bin)** — select this complete, headered file in the flasher.
- **[Download SHA256SUMS.txt](https://github.com/pranavms13/niimbot-d110m-patched-firmware/releases/download/v4.31-history-reset-r1/SHA256SUMS.txt)** — checksum for the release firmware above. Download both files into the same folder and run `shasum -a 256 -c SHA256SUMS.txt` on macOS.
- [Release notes](https://github.com/pranavms13/niimbot-d110m-patched-firmware/releases/tag/v4.31-history-reset-r1).
- [Original D110_M 4.31 update image](https://github.com/pranavms13/niimbot-d110m-patched-firmware/raw/refs/heads/main/firmware/D110_M_V4.31_original.bin) — retained for comparison and possible stock restoration if the updater remains reachable. It is not a full-device backup or guaranteed recovery image.
- [Repository checksums for both firmware images](firmware/SHA256SUMS.txt) and [patch manifest](firmware/patch-manifest.json).

The patched download's SHA-256 is:

```text
909fe39cf7176e54999fb5a113f94c6792d503b9578362a1a79e00200564ecc8
```

**D110 and D110_M are different models.** This image is for model ID `2320` (`0x0910`), based on version **4.31**. It continues to report **4.31** after installation; the patch does not change the version display.

## Why r1 needs two resets

The sticker stores a used-label counter, and the printer remembers the largest count it has seen for that roll. Resetting only the sticker can leave the printer showing its remembered count. Stock factory reset preserves that history.

The r1 patch changes factory reset command `0x28` to clear the 20 remembered roll records before saving settings. It retains the normal factory-default changes. It does **not** reset the sticker, disable NFC authentication, or remove label limits.

Follow the [r1 quick reset steps above](#quick-reset-published-r1-firmware-and-iphone) for each refill, or use the [full reset guide](docs/RESET.md) for detailed response checks and troubleshooting.

## Repository contents

```text
firmware/                   Patched and original update files, manifest, hashes
docs/RESET.md               Everyday refill/reset steps
docs/FLASHING.md            First-time installation and restoration limits
docs/TECHNICAL.md           Patch layout, NFC format, build commands
docs/VERIFICATION.md        Offline and physical test evidence
patch_firmware.py           Offline, hash-pinned firmware patch builder
niimbot_tag.py              Offline NFC counter inspector and command generator
verification/              Portable function-level checks and anonymized results
```

The original Python utilities build or inspect files. The experimental Bluetooth client connects to the printer and can reset it, but does not flash firmware. The device-specific scripts used for the original physical test and the raw device logs are not included.

## References

- [NiimBlue author's flashing instructions](https://github.com/MultiMote/niimblue/wiki/Flashing-firmwares)
- [NIIMBOT firmware header format](https://printers.niim.blue/firmware/)
- [D110_M hardware notes](https://printers.niim.blue/hardware/niimbot-d110_m/)
- [NFC Tools advanced-command instructions](https://www.wakdev.com/en/knowledge-base/how-to-guides/how-to-use-advanced-nfc-commands.html)

NIIMBOT's original firmware remains third-party material. This repository is not affiliated with NIIMBOT and does not claim ownership of the original firmware.
