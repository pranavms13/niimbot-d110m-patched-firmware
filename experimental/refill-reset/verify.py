"""Run compiled ARM extension + stock crypto/settings writer in Unicorn.

NFC, flash erase/program/read, allocator, transport, clock and reset-register
effects are simulated. No hardware connection or physical reboot is tested.
"""
import json
from collections import deque
from pathlib import Path
import random
import struct
import sys
from zlib import crc32

from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11, UC_ARM_REG_LR, UC_ARM_REG_SP, UC_ARM_REG_PC

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT/'verification')]
from niimbot_tag import encrypt, decrypt, counter_block
from decompress import decompress_initializer
from patch_firmware import validate_container, BASE
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

OUTPUT = ROOT/'build/refill-reset'
manifest = json.loads((OUTPUT/'manifest.json').read_text())
image = (OUTPUT/manifest['image']).read_bytes()
FW = image[28:]
assert validate_container(image) == (431, 2320)
original = (ROOT/'firmware/D110_M_V4.31_original.bin').read_bytes()[28:]
allowed = {i for p in [0x4eee,0x4efc,0x7388] for i in range(p,p+4)}
assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(original,FW)))
assert len(FW) == manifest['extension_offset']+manifest['extension_bytes']
decoder = Cs(CS_ARCH_ARM,CS_MODE_THUMB); decoder.detail=True
for hook in manifest['hooks']:
    insn=next(decoder.disasm(FW[hook['offset']:hook['offset']+4],BASE+hook['offset']))
    assert insn.mnemonic=='bl' and insn.operands[0].imm==hook['target']
UID = bytes.fromhex('8804112233445566')
MAGIC = b'REFILL\x01\xa5'
STOP = 0x0100f000
ARGS = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3]
SAVED = [UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11]


class Device:
    def __init__(self, reserved=0, used=7):
        self.u = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
        for addr, size in [(0x20000, 0x50000), (0xf0000, 0x10000),
                           (STOP, 0x1000), (BASE, 0x20000), (0x010ff000, 0x1000)]:
            self.u.mem_map(addr, size)
        self.u.mem_write(BASE, FW)
        self.u.mem_write(0x20004, decompress_initializer(FW))
        # Initialize the dispatch index exactly from the recovered 45-entry table.
        self.u.mem_write(0x203b4, struct.pack('<II', 0x20184, 45))
        self.u.mem_write(0x203bc, bytes([45])*256)
        for i in range(45):
            cmd = struct.unpack('<I', self.read(0x20184+12*i, 4))[0]
            self.u.mem_write(0x203bc+cmd, bytes([i]))
        self.u.mem_write(0x207d0, b'\x02')
        self.u.mem_write(0x203a4, b'\x07')
        rng = random.Random(reserved + used)
        plain = bytearray(rng.randrange(256) for _ in range(120))
        plain[:4] = struct.pack('<HH', reserved, used)
        plain[4:8] = struct.pack('<I', crc32(plain[:4]))
        plain[8:16] = UID
        plain[66:68] = struct.pack('<H', 186)
        plain[116:] = struct.pack('<I', crc32(plain[8:116]))
        self.tag = bytearray(180)
        self.tag[20:140] = b''.join(encrypt(plain[i:i+8]) for i in range(0, 120, 8))
        self.original_tag = bytes(self.tag)
        self.uid = UID
        settings = bytearray(rng.randrange(256) for _ in range(316))
        settings[:4] = struct.pack('<I', crc32(settings[4:]))
        self.settings = bytes(settings)
        self.u.mem_write(0x20900, self.settings)
        self.u.mem_write(0x010ff000, self.settings)
        self.u.mem_write(0x48308, bytes(plain[:8]))
        self.u.mem_write(0x20782, b'\x03\x00\x05\x00')
        self.auth_calls = self.read_calls = self.write_calls = 0
        self.flash_calls = self.send_calls = 0
        self.power = []; self.responses = []; self.events = []
        self.field_on = False; self.selected = False
        self.write_fail = set(); self.read_fail = set(); self.auth_fail = set()
        self.corrupt_write = set(); self.swap_auth = set()
        self.flash_fail = False; self.reboot = False
        self.elapsed_calls = 0; self.lowest_sp = 0x6f000
        self.trace = deque(maxlen=12)
        self.u.hook_add(UC_HOOK_CODE, self.code)
        self.u.hook_add(UC_HOOK_MEM_WRITE, self.memory_write)

    def read(self, a, n): return bytes(self.u.mem_read(a, n))
    def arg(self, n): return self.u.reg_read(ARGS[n])
    def ret(self, value=0):
        self.u.reg_write(UC_ARM_REG_R0, value & 0xffffffff)
        self.u.reg_write(UC_ARM_REG_PC, self.u.reg_read(UC_ARM_REG_LR))

    def memory_write(self, uc, access, address, size, value, _):
        if address == 0xf857c:
            assert value == 0x55 and self.read(0xf8574, 1)[0] & 1
            assert self.responses and self.responses[-1][7] == 0
            assert self.events.index('flash') < self.events.index('send')
            assert self.elapsed_calls >= 2
            self.events.append('reboot'); self.reboot = True
            uc.emu_stop()

    def code(self, uc, address, size, _):
        self.trace.append(hex(address))
        self.lowest_sp = min(self.lowest_sp, uc.reg_read(UC_ARM_REG_SP))
        if address == STOP: uc.emu_stop(); return
        off = address - BASE
        if off == 0x7252:
            mode = self.arg(1)
            self.power.append(mode)
            self.field_on = mode == 3
            if not self.field_on: self.selected = False
            self.ret()
        elif off == 0x533c:
            self.auth_calls += 1
            assert self.field_on and not self.selected, 'Reselection needs a fresh NFC field state'
            if self.auth_calls in self.auth_fail: self.ret(0xf4); return
            self.selected = True
            uid = bytes.fromhex('8804998877665544') if self.auth_calls in self.swap_auth else self.uid
            uc.mem_write(self.arg(1), uid); uc.mem_write(self.arg(2), bytes([len(uid)])); self.ret()
        elif off == 0x541c:
            self.read_calls += 1
            if self.read_calls in self.read_fail: self.ret(0xf4); return
            page = self.arg(1)
            assert 5 <= page <= 33
            uc.mem_write(self.arg(2), bytes(self.tag[page*4:page*4+16])); self.ret()
        elif off == 0x556a:
            self.write_calls += 1
            page = self.arg(1)
            assert page in (5, 6), 'Attempt to write outside counter pages'
            if self.write_calls in self.write_fail: self.ret(0xf4); return
            data = bytearray(self.read(self.arg(2), 4))
            if self.write_calls in self.corrupt_write: data[0] ^= 1
            self.tag[page*4:page*4+4] = data
            self.ret()
        elif off == 0xc6f0:
            # Do not stub the high-level writer: execute its erase/program,
            # readback comparison, retries, and success/error returns.
            self.flash_calls += 1; self.events.append('flash')
        elif off == 0xe2b8: self.ret(0x61000)  # malloc for flash readback
        elif off == 0xc7e0: self.ret()  # free
        elif off == 0x118ac:
            if not self.flash_fail: uc.mem_write(self.arg(0), bytes([255])*4096)
            self.ret()
        elif off == 0xc678:
            if not self.flash_fail: uc.mem_write(self.arg(0), self.read(self.arg(1), self.arg(2)))
            self.ret()
        elif off == 0xc664:
            uc.mem_write(self.arg(1), self.read(self.arg(0), self.arg(2))); self.ret()
        elif off == 0x4dc4:
            self.responses.append(self.read(self.arg(0), self.arg(1)))
            self.send_calls += 1; self.events.append('send'); self.ret()
        elif off == 0x78c8: self.ret(123)
        elif off == 0x78d4:
            assert self.arg(0) == 123 and self.arg(1) == 500
            self.elapsed_calls += 1; self.ret(self.elapsed_calls >= 2)

    def command(self, cmd=0xf0, data=MAGIC+UID, allow_no_reply=False):
        self.u.mem_write(0x68000, bytes([0, 0, 1, cmd, len(data)])+data)
        self.u.reg_write(UC_ARM_REG_SP, 0x6f000)
        self.u.reg_write(UC_ARM_REG_LR, STOP | 1)
        for reg in SAVED: self.u.reg_write(reg, 0x11223000 + reg)
        for reg, value in zip(ARGS, [0x68000, 0x69000, 0x6a000, 1]): self.u.reg_write(reg, value)
        # Execute the complete outer stock command handler through both hooks.
        try:
            self.u.emu_start((BASE+0x4ec0)|1, STOP, count=2000000)
        except Exception:
            print('Emulator failure: PC', hex(self.u.reg_read(UC_ARM_REG_PC)),
                  'LR', hex(self.u.reg_read(UC_ARM_REG_LR)), 'trace', list(self.trace))
            raise
        assert self.u.reg_read(UC_ARM_REG_PC) == STOP or self.reboot
        if not self.reboot:
            assert self.u.reg_read(UC_ARM_REG_SP) == 0x6f000
            for reg in SAVED: assert self.u.reg_read(reg) == 0x11223000+reg
        if allow_no_reply and not self.responses: return None
        assert self.responses
        frame = self.responses[-1]
        checksum = 0
        for b in frame[2:-3]: checksum ^= b
        assert frame[:2] == b'\x55\x55' and frame[-2:] == b'\xaa\xaa'
        assert checksum == frame[-3]
        return frame[7] if cmd == 0xf0 else frame


checks = 0
def passed(message):
    global checks
    checks += 1; print('PASS:', message)

for reserved, used in [(0, 7), (0x1234, 186), (65535, 65535), (0, 0)]:
    d = Device(reserved, used)
    assert d.command() == 0 and d.reboot
    assert d.tag[20:28] == counter_block(reserved, 0)
    assert d.tag[:20]+d.tag[28:] == d.original_tag[:20]+d.original_tag[28:]
    saved = d.read(0x010ff000, 316)
    expected = bytearray(d.settings)
    for index, value in [(4,3),(5,3),(7,3),(6,1),(8,1),(0x128,1),(0x129,1),(0x130,2)]: expected[index]=value
    expected[0x28:0x11c] = bytes(244)
    expected[:4] = struct.pack('<I',crc32(expected[4:]))
    assert saved == bytes(expected) == d.read(0x20900, 316)
    baseline = Device(reserved,used)
    baseline.command(0x28,b'\x01')
    assert saved == baseline.read(0x010ff000,316)
    assert d.read(0x4830a, 2) == bytes(2)
    assert d.read(0x20782, 4) == bytes(4)
    assert d.power == [0,3,0,3,0] and d.write_calls == 2
    assert d.lowest_sp >= 0x6f000-2048
passed('4 counter/reserved combinations: tag, settings match actual stock-defaults/r1 path, flash readback, reply then reboot')

d=Device(); assert d.command(data=b'\x00')==0x10 and not d.reboot
assert d.auth_calls==d.flash_calls==d.write_calls==0 and d.power==[]
passed('read-only capability query has no NFC, settings or reboot side effects')
for data in [b'', b'R', b'REFILL', MAGIC, MAGIC+UID+b'\x00', b'X'+(MAGIC+UID)[1:]]:
    d=Device(); assert d.command(data=data)==1 and not d.reboot
    assert d.auth_calls==d.flash_calls==d.write_calls==0
passed('malformed and truncated custom requests cause no writes')
d=Device(); d.u.mem_write(0x207d0,b'\x01')
assert d.command(allow_no_reply=True) is None and d.auth_calls==d.flash_calls==0
for address, value in [(0x203a4,1),(0x203a4,2),(0x21cf1,1),(0x21cec,1),
                       (0x204d5,1),(0x207f0,1),(0x207c8,1),(0x207ec,1)]:
    d=Device(); d.u.mem_write(address, bytes([value]))
    assert d.command()==2 and not d.reboot and d.auth_calls==d.flash_calls==0
passed('9 inactive-device, print, motion and update guards reject without NFC writes')
for field, value, status in [('auth_fail',{1},3),('auth_fail',{2},3),
                              ('read_fail',{1},3),('read_fail',{8},3),
                              ('swap_auth',{1},5),('swap_auth',{2},5)]:
    d=Device(); setattr(d,field,value)
    assert d.command()==status and not d.reboot and d.write_calls==d.flash_calls==0
    assert bytes(d.tag)==d.original_tag and d.power[-1]==0
passed('authentication/read failures and tag swaps before writing abort cleanly')
for at in [20,36]:
    d=Device(); d.tag[at]^=1
    assert d.command()==4 and not d.reboot and d.write_calls==d.flash_calls==0
passed('independent counter and metadata CRC checks reject corruption')
d=Device(); assert d.command(data=MAGIC+bytes(8))==5 and d.write_calls==0
d=Device(); plain=bytearray(b''.join(decrypt(d.tag[i:i+8]) for i in range(20,140,8)))
plain[8]^=1; plain[116:]=struct.pack('<I',crc32(plain[8:116]))
d.tag[20:140]=b''.join(encrypt(plain[i:i+8]) for i in range(0,120,8))
assert d.command()==5 and d.write_calls==0
passed('expected roll ID and physical-versus-encrypted identity must both match')
for which in [1,2]:
    d=Device(); d.write_fail={which}
    assert d.command()==6 and not d.reboot and d.flash_calls==0
    assert bytes(d.tag)==d.original_tag
passed('either NFC page-write failure restores and verifies original counter')
for kind in ['corrupt','read_error']:
    d=Device()
    if kind=='corrupt': d.corrupt_write={2}
    else: d.read_fail={9}
    assert d.command()==7 and not d.reboot and d.flash_calls==0
    assert bytes(d.tag)==d.original_tag
passed('bad/missing readback restores the original counter before reporting failure')
d=Device(); d.write_fail={2,3,4}
assert d.command()==9 and not d.reboot and d.flash_calls==0
d=Device(); d.write_fail={2}; d.swap_auth={3}
assert d.command()==9 and d.write_calls==2 and not d.reboot
passed('unverified rollback is reported; swapped tag is never written during rollback')
d=Device(); d.flash_fail=True
assert d.command()==8 and not d.reboot and d.flash_calls==1
assert d.read(0x20900,316)==d.settings
assert d.tag[20:28]==counter_block(0,0)
passed('stock flash writer retries and reports failure; no false success or reboot')
d=Device(); frame=d.command(0x28,b'\x01')
assert frame==bytes.fromhex('555538010138aaaa') and not d.reboot
assert d.auth_calls==0 and d.read(0x20928,244)==bytes(244)
passed('ordinary factory reset still follows the original r1 path without touching NFC or rebooting')
print(f'{checks} groups passed. Hardware timing, physical NFC and actual reboot remain unverified.')
