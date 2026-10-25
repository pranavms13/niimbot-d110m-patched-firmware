# NIIMBOT D110_M: factory reset clears roll history

A small patch to **D110_M firmware 4.31** that makes factory reset erase the printer's saved roll history. Combined with resetting the NFC sticker's counter, this allowed a tested sticker to be reused on a replacement reel.

**Tested on one D110_M with hardware 4.01.** The patched firmware was installed over Bluetooth, history clearing survived a power cycle, and the owner confirmed a clear test print on the replacement reel. The used count advanced from **0 to 1**. See [verification results](docs/VERIFICATION.md).

This is an unofficial firmware modification. A failed update or incompatible image can leave a printer unable to boot. Compatibility with other models or hardware versions has not been established, and Bluetooth recovery is not guaranteed.

## Start here

| What you need | Instructions |
| --- | --- |
| Reset a reel on an **already patched printer** | [Reset the printer and NFC sticker](docs/RESET.md) |
| Install the patch for the first time | [Flash over Bluetooth from a Mac](docs/FLASHING.md) |
| Understand the change or rebuild it | [Technical details and reproducible build](docs/TECHNICAL.md) |
| See what was actually tested | [Verification](docs/VERIFICATION.md) |

## Downloads

- **[GitHub release: firmware and checksum](https://github.com/pranavms13/niimbot-d110m-patched-firmware/releases/tag/v4.31-history-reset-r1)** — download the `.bin` and `SHA256SUMS.txt` assets together.
- **[Patched D110_M 4.31 firmware](https://github.com/pranavms13/niimbot-d110m-patched-firmware/raw/refs/heads/main/firmware/D110_M_V4.31_history-reset.bin)** — select this complete, headered file in the flasher.
- [Original D110_M 4.31 update image](https://github.com/pranavms13/niimbot-d110m-patched-firmware/raw/refs/heads/main/firmware/D110_M_V4.31_original.bin) — retained for comparison and possible stock restoration if the updater remains reachable. It is not a full-device backup or guaranteed recovery image.
- [SHA-256 checksums](firmware/SHA256SUMS.txt) and [patch manifest](firmware/patch-manifest.json).

The patched download's SHA-256 is:

```text
909fe39cf7176e54999fb5a113f94c6792d503b9578362a1a79e00200564ecc8
```

**D110 and D110_M are different models.** This image is for model ID `2320` (`0x0910`), based on version **4.31**. It continues to report **4.31** after installation; the patch does not change the version display.

## Why two resets are necessary

The sticker stores a used-label counter, and the printer remembers the largest count it has seen for that roll. Resetting only the sticker can leave the printer showing its remembered count. Stock factory reset preserves that history.

This patch changes factory reset command `0x28` to clear the 20 remembered roll records before saving settings. It retains the normal factory-default changes. It does **not** reset the sticker, disable NFC authentication, or remove label limits.

For each refill:

1. Remove the roll and sticker from the printer.
2. With the printer on, connect in NiimBlue and select **gear → Tests → Reset**.
3. Turn the printer off and reset the sticker with NFC Tools.
4. Attach the sticker to the matching replacement reel, load it, and turn the printer on.

The exact NFC commands and response checks are in [RESET.md](docs/RESET.md). **No repeat firmware flashing is needed for future refills.**

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

The included Python utilities build or inspect files; they do not connect to or flash a printer. The device-specific scripts used for the physical test and the raw device logs are not included.

## References

- [NiimBlue author's flashing instructions](https://github.com/MultiMote/niimblue/wiki/Flashing-firmwares)
- [NIIMBOT firmware header format](https://printers.niim.blue/firmware/)
- [D110_M hardware notes](https://printers.niim.blue/hardware/niimbot-d110_m/)
- [NFC Tools advanced-command instructions](https://www.wakdev.com/en/knowledge-base/how-to-guides/how-to-use-advanced-nfc-commands.html)

NIIMBOT's original firmware remains third-party material. This repository is not affiliated with NIIMBOT and does not claim ownership of the original firmware.
