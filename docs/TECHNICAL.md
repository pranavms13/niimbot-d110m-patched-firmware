# Patch design and reproducible build

## Firmware change

All offsets below refer to the **raw application payload**, after the 28-byte update header. The application code base is `0x01010000`.

| Location | Purpose |
| --- | --- |
| `0x7374` | Factory-reset handler for command `0x28` |
| `0x7388` | The original call to settings save; replaced with a call to the new wrapper |
| `0x125d8` | Original factory-default settings function, unchanged |
| `0x12e20` | Original CRC/settings-save function, unchanged |
| `0x182` | Existing memory-zero routine |
| `0x1c724` | Appended 20-byte wrapper |

The wrapper receives the existing settings pointer in `r0`:

```asm
push {r4, lr}
mov  r4, r0
adds r0, #0x28
movs r1, #0xf4
bl   0x01010182       ; clear 244 history bytes
mov  r0, r4
bl   0x01022e20       ; original CRC/settings save
pop  {r4, pc}
```

History lives at RAM `0x20928..0x20a1b`: a four-byte insertion header and twenty 12-byte entries. Settings are persisted at flash address `0x010ff000`.

Only one four-byte call changes inside the original application. The wrapper is appended without moving existing code/data and remains within the original last 256-byte flash page. The payload grows from **116,516 to 116,536 bytes**. Its update header gets a new length, payload CRC32, and header CRC32. Model ID and version remain unchanged.

The patch does not alter NFC authentication, tag encryption, metadata, label limits, or normal count increments. It clears history only when factory reset is explicitly requested. Use it with the roll removed and power-cycle before reinserting the zero-counter tag.

## Build

Python 3.9 or newer is sufficient for the builder; no third-party packages are required.

From the repository root:

```bash
python3 patch_firmware.py firmware/D110_M_V4.31_original.bin --output-dir build
cmp build/D110_M_V4.31_history-reset.bin firmware/D110_M_V4.31_history-reset.bin
```

The builder checks the container CRCs, model, version, exact payload size, and original application SHA-256 before editing. It rejects a different firmware, malformed input, or a raw application without its update header. It does not open a Bluetooth/NFC connection.

Original application SHA-256:

```text
334260a24c516507386bd6cf99b7735bffb12a200b2354070c1878b627181e84
```

The optional `--transport-version` argument changes only the update-header version within the 4.31–4.99 range. It does not update the application's reported version or establish compatibility. The physically tested and published image uses the default **4.31**.

## Run the offline checks

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-verification.txt
python verification/verify_firmware.py
python verification/verify_patch.py
python verification/verify_upload.py
```

These checks use a deliberately limited Thumb interpreter and Capstone to execute selected functions from the actual binary. Peripheral operations are substituted where documented. This is not a complete Cortex-M/device emulator; see [verification scope](VERIFICATION.md).

The public tests use synthetic identities. They do not require a printer, NFC sticker, local home-directory paths, or the device-specific Bluetooth scripts used during development.

## NFC counter format

For the analyzed sticker format, pages `05` and `06` contain one encrypted eight-byte counter record:

```text
uint16 preserved/reserved
uint16 used_count
uint32 CRC32(first four plaintext bytes)
```

The record uses little-endian words and 32-round TEA. The key words recovered from this firmware are:

```text
0000CCA1 000072B7 00006758 000065C9
```

The tested password is `12 34 56 78` and its authentication response is `55 55`. Zero reserved bytes and zero used encrypt to `74 2F C7 63 E0 17 DB F9`.

`niimbot_tag.py` validates the record CRC, preserves the first two bytes, and generates reset, readback, and restoration commands. It never writes to a sticker itself. See [RESET.md](RESET.md) for the exact workflow and applicability limits.

The printer's stock history lookup restores the larger of tag usage and saved usage. That is why an acknowledged NFC write and a correct zero-counter readback can coexist with the printer still displaying an old count.

## References

- [Update container format](https://printers.niim.blue/firmware/), independently checked against the included image.
- [NiimBlue packet encoding](https://github.com/MultiMote/niimbluelib/blob/main/src/packets/packet.ts) and [update flow](https://github.com/MultiMote/niimbluelib/blob/main/src/packets/protocol.ts).
- [NXP NTAG213/215/216 data sheet](https://www.nxp.com/docs/en/data-sheet/NTAG213_215_216.pdf) for NFC commands and lock behavior.
