# NIIMBOT D110_M: factory reset clears roll history

A small patch to **D110_M firmware 4.31** that makes factory reset erase the printer's saved roll history. Combined with resetting the NFC sticker's counter, this allowed a tested sticker to be reused on a replacement reel.

**Tested on one D110_M with hardware 4.01.** The patched firmware was installed over Bluetooth, history clearing survived a power cycle, and the owner confirmed a clear test print on the replacement reel. The used count advanced from **0 to 1**. See [verification results](docs/VERIFICATION.md).

This is an unofficial firmware modification. A failed update or incompatible image can leave a printer unable to boot. Compatibility with other models or hardware versions has not been established, and Bluetooth recovery is not guaranteed.

## Quick reset for each refill

**The patched firmware must already be installed. You do not need to flash it again.** Reset both the printer's history and the NFC sticker:

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

## Experimental combined reset over Bluetooth

A separate [experimental firmware and Mac client](experimental/refill-reset/README.md) add one command that resets the loaded sticker, clears history/restores defaults, and requests a reboot. On one printer, **counter reset and persistence passed, but automatic restart failed: pressing power was necessary**. The published r1 release does not support this command; the combined reset remains experimental.

## Start here

| What you need | Instructions |
| --- | --- |
| Reset a reel on an **already patched printer** | [Reset the printer and NFC sticker](docs/RESET.md) |
| Install the patch for the first time | [Flash over Bluetooth from a Mac](docs/FLASHING.md) |
| Understand the change or rebuild it | [Technical details and reproducible build](docs/TECHNICAL.md) |
| See what was actually tested | [Verification](docs/VERIFICATION.md) |

## Downloads

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

## Why two resets are necessary

The sticker stores a used-label counter, and the printer remembers the largest count it has seen for that roll. Resetting only the sticker can leave the printer showing its remembered count. Stock factory reset preserves that history.

This patch changes factory reset command `0x28` to clear the 20 remembered roll records before saving settings. It retains the normal factory-default changes. It does **not** reset the sticker, disable NFC authentication, or remove label limits.

Follow the [quick reset steps above](#quick-reset-for-each-refill) for each refill, or use the [full reset guide](docs/RESET.md) for detailed response checks and troubleshooting.

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
