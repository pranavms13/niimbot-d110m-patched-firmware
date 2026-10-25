"""Execute original and patched reset paths; simulate only peripheral I/O."""
import json
import random
import struct
import sys
from pathlib import Path
from zlib import crc32

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from verify_firmware import BASE, FW, Thumb
from patch_firmware import build, validate_container, APP_SIZE, CALL_OFFSET

ROOT = Path(__file__).resolve().parent.parent
ORIGINAL = (ROOT/'firmware/D110_M_V4.31_original.bin').read_bytes()
IMAGE = (ROOT/'firmware/D110_M_V4.31_history-reset.bin').read_bytes()
PATCHED = IMAGE[28:]
assert ORIGINAL[28:] == FW
assert build(ORIGINAL)[0] == IMAGE
assert validate_container(IMAGE) == (431, 2320)
assert PATCHED[:CALL_OFFSET] == FW[:CALL_OFFSET]
assert PATCHED[CALL_OFFSET+4:APP_SIZE] == FW[CALL_OFFSET+4:]
assert len(PATCHED)-len(FW) == 20
print('PASS: deterministic build, original hash, payload/header CRCs, model and version.')
print('PASS: only the 4-byte save call changes in the original payload; 20 bytes appended.')

# Decode every new instruction with Capstone, independent of the BL encoder.
decoder=Thumb(PATCHED).md
stub=list(decoder.disasm(PATCHED[APP_SIZE:], BASE+APP_SIZE))
assert [i.mnemonic for i in stub] == ['push','mov','adds','movs','bl','mov','bl','pop']
assert [i.operands[0].imm for i in stub if i.mnemonic=='bl'] == [BASE+0x182,BASE+0x12e20]
branch=next(decoder.disasm(PATCHED[CALL_OFFSET:CALL_OFFSET+4],BASE+CALL_OFFSET))
assert branch.mnemonic=='bl' and branch.operands[0].imm==BASE+APP_SIZE
print('PASS: independent Thumb decode confirms wrapper, memset call, save call, and redirect.')
for i in stub:
    print(f'  {i.address:08x}: {i.mnemonic} {i.op_str}')

def setup(firmware, settings):
    vm=Thumb(firmware)
    vm.write(0x208f0,bytes([0x9a])*16)
    vm.write(0x20900,settings)
    vm.write(0x20a3c,bytes([0xa9])*16)
    vm.flash_writes=[]; vm.responses=[]; vm.logs=[]
    def flash(t):
        address,source,size=t.reg('r0'),t.reg('r1'),t.reg('r2')
        assert address==0x010ff000 and size==0x13c
        data=t.read(source,size)
        t.flash_writes.append((address,data));t.write(address,data);t.put('r0',0)
    def send(t):
        p=t.reg('r0')
        t.responses.append((t.read(p+3,3),t.reg('r1'),t.reg('r2')))
    vm.hooks[BASE+0xc6f0]=flash
    vm.hooks[BASE+0x4e18]=send
    vm.hooks[BASE+0xe13c]=lambda t:t.logs.append((t.reg('r0'),t.reg('r1')))
    vm.hooks[BASE+0xc664]=lambda t:t.write(t.reg('r1'),t.read(t.reg('r0'),t.reg('r2')))
    return vm

rng=random.Random(431)
for trial in range(12):
    data=bytearray(rng.randrange(256) for _ in range(0x13c))
    # Valid settings with deliberately nonempty history.
    struct.pack_into('<I',data,0,crc32(data[4:]))
    original=setup(FW,data);patched=setup(PATCHED,data)
    saved_regs={f'r{i}':0x11223000+i for i in range(4,12)}
    for vm in (original,patched):
        for name,value in saved_regs.items():vm.put(name,value)
        assert vm.call(0x7374,0x60000,0x1234,0x5678)==1
        assert vm.reg('sp')==0x6f000
        assert all(vm.reg(k)==v for k,v in saved_regs.items())
        assert vm.read(0x208f0,16)==bytes([0x9a])*16
        assert vm.read(0x20a3c,16)==bytes([0xa9])*16
        assert vm.responses==[(b'\x38\x01\x01',0x1234,0x5678)]
        assert not vm.logs
        assert len(vm.flash_writes)==1
        image=vm.flash_writes[0][1]
        assert crc32(image[4:])==int.from_bytes(image[:4],'little')
    assert original.read(0x20928,0xf4)==data[0x28:0x11c]
    assert patched.read(0x20928,0xf4)==bytes(0xf4)
    # The factory defaults and every other persisted setting stay identical
    # to an unmodified reset. CRC naturally differs after clearing history.
    assert original.read(0x20904,0x24)==patched.read(0x20904,0x24)
    assert original.read(0x20a1c,0x20)==patched.read(0x20a1c,0x20)
    assert patched.flash_writes[0][1][0x28:0x11c]==bytes(0xf4)
    # Load persisted settings through the original loader/CRC code.
    persisted=patched.flash_writes[0][1]
    patched.write(0x20900,bytes([0xff])*0x13c)
    patched.call(0xd128,0x20900)
    assert patched.read(0x20900,0x13c)==persisted
    assert not patched.logs
    # Reset again with already-empty history: avoids another flash write.
    patched.call(0x7374,0x60000,0x1234,0x5678)
    assert len(patched.flash_writes)==1
print('PASS: 12 varied settings/history records clear and persist exactly 244 history bytes.')
print('PASS: defaults, adjacent settings, stack/registers and reset response are preserved.')
print('PASS: actual firmware CRC/save/load paths preserve empty history across simulated restart.')
print('PASS: repeated reset with unchanged settings does not cause another flash write.')

# History lookup after the reset accepts the a synthetic zero-count sticker.
patched.write(0x48310,bytes.fromhex('8804112233445566'))
patched.write(0x4830a,bytes(2))
patched.write(0x4834a,struct.pack('<H',186))
patched.write(0x207e4,bytes(4))
patched.hooks[BASE+0x204]=lambda t:t.put('r0',int(t.read(t.reg('r0'),t.reg('r2'))!=t.read(t.reg('r1'),t.reg('r2'))))
def divide(t):
    quotient,remainder=divmod(t.reg('r0'),t.reg('r1'))
    t.put('r0',quotient);t.put('r1',remainder)
patched.hooks[BASE+0xfc]=divide
patched.call(0x14d74,0)
assert patched.read(0x4830a,2)==bytes(2)
assert patched.read(0x2092c,8)==bytes.fromhex('8804112233445566')
assert patched.read(0x20936,2)==bytes(2)
assert int.from_bytes(patched.read(0x207e4,4),'little')&(1<<19)==0
print('PASS: history lookup accepts the synthetic identity at zero after reset/reload.')

for invalid in (ORIGINAL[28:], ORIGINAL[:-1], ORIGINAL[:50]+bytes([ORIGINAL[50]^1])+ORIGINAL[51:]):
    try:build(invalid)
    except ValueError:pass
    else:raise AssertionError('Invalid input accepted')
print('PASS: builder rejects raw payload, truncation, and corruption.')
print('LIMIT: no physical flash, bootloader execution, radio/peripheral emulation, or print test.')
