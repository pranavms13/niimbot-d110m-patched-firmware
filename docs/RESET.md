# Reset a reel after installing the patch

You must reset **both the printer's saved history and the NFC sticker**. These instructions assume the [patched firmware](FLASHING.md) is already installed. You do not need to flash it again.

## 1. Remove the reel

Remove the reel and its NFC sticker from the printer. Close or disconnect the NIIMBOT phone app so the Mac can connect.

## 2. Reset the printer's saved history

1. Turn the printer **on**, with the roll/sticker still removed.
2. On the Mac, open [NiimBlue](https://niim.blue) in **Google Chrome**.
3. Select Bluetooth, click **Connect**, and choose the D110_M.
4. Open **gear → Tests → Reset** and wait for the command to finish.
5. Turn the printer **off**.

The patched reset clears **all remembered rolls** and also restores the ordinary factory settings. Removing the roll and restarting prevents active-roll RAM state from retaining the old count.

## 3. Reset the NFC sticker

Keep the printer **off** during the phone scan.

The fixed write batch below was verified on the sticker used in this project. It assumes the D110_M counter format, password `12 34 56 78`, and zero in the first two decrypted counter-record bytes. It is not a universal command for every NIIMBOT sticker. For another sticker, first follow the validation section below.

On the iPhone, open **NFC Tools → Other → Advanced NFC commands**, paste this entire line, and hold the sticker at the top of the phone until all commands finish:

```text
1B:12:34:56:78,A2:05:74:2F:C7:63,A2:06:E0:17:DB:F9,30:05
```

Expected responses, in order:

```text
55 55                 Authentication succeeded
0A                    Page 05 write accepted
0A                    Page 06 write accepted
74 2F C7 63 E0 17 DB F9 ...
                      Readback: the first eight bytes encode zero used
```

The final read returns 16 bytes. Only its first eight bytes should match the counter shown above; the following eight bytes are unchanged metadata.

If authentication or either write fails, stop and retain the responses. Do not try random passwords or write lock/configuration pages. Keep the sticker in place throughout the batch; the two page writes are not atomic.

## 4. Load the replacement reel

Attach the same sticker to a replacement reel matching the original label size/type, load it, close the lid, and turn the printer **on**. Reconnect and refresh roll information. It should show **0 used labels**. A one-label print should then show **1 used**.

The test in this repository used a matching **12 × 40 mm** roll. The sticker's size/type metadata still applies; resetting counters does not reconfigure those fields.

## Read or validate another sticker before writing

With the printer off, this batch authenticates and reads without changing tag memory:

```text
1B:12:34:56:78,30:05
```

Save the complete response as a backup. Pass the **first eight bytes of the `30 05` response** to the offline utility, replacing the example below with your own bytes:

```bash
python3 niimbot_tag.py --counter-hex '74 2F C7 63 E0 17 DB F9'
```

The utility checks the decrypted counter CRC, preserves the first two bytes, and outputs:

- `nfc_tools_batch`: a batch suitable for NFC Tools;
- the expected zero-counter readback;
- the original bytes and commands to restore them.

If it reports a CRC mismatch, do not use the fixed write batch. A valid counter CRC alone does not prove that a different sticker has the same full metadata, lock map, or printer compatibility. A supported full tag dump can also be checked with `--dump` as described by `--help`.

## If the old count remains

- Confirm the patched firmware was installed; its displayed version intentionally remains **4.31**.
- Confirm that **both** resets were done, with the roll removed for the printer reset.
- Power off and read `30 05` again. If the first eight bytes are the expected zero block but the printer shows the old count, check the printer reset and refresh the app's data.
- If the tag no longer reads zero, its counter needs resetting again while the printer is off.

The complete process was physically verified: history changed from one record with seven used labels to zero records, stayed empty after a power cycle, and the replacement reel printed clearly with a count of zero advancing to one.
