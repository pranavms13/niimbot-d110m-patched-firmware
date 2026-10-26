"""Offline transport/parser checks; no Bluetooth hardware imports or calls."""
import asyncio
from bluetooth_refill import Connection, packet, refill_payload, decode_roll

uid=bytes.fromhex('8804112233445566')
assert packet(0xf0,b'\x00')==bytes.fromhex('5555f00100f1aaaa')
raw=packet(0xf0,refill_payload(uid))
assert len(raw)==23 and raw[3]==16 and raw[12:20]==uid
try: refill_payload(uid[1:])
except ValueError: pass
else: raise AssertionError('7-byte phone UID accepted')
print('PASS: exact probe frame, 23-byte reset frame and rejection of 7-byte UID')

reply=packet(0xf1,b'RF\x01\x10')
for split in range(1,len(reply)):
    c=Connection(None)
    c.notify(None,reply[:split]); assert c.queue.empty()
    c.notify(None,reply[split:]); assert c.queue.get_nowait()==(0xf1,b'RF\x01\x10')
c=Connection(None); c.notify(None,b'noise'+reply+reply)
assert c.queue.qsize()==2
bad=bytearray(reply); bad[-3]^=1
c=Connection(None); c.notify(None,bad)
assert isinstance(c.queue.get_nowait(),ValueError)
print('PASS: all reply fragmentation points, coalescing, leading noise and corrupt checksum')

roll=uid+b'\x03ABC\x02DE\x00\xba\x00\x07\x01'
assert decode_roll(roll)=={'identity':uid.hex(),'limit':186,'used':7,'type':1}
for data in [b'\x00',roll[:9],roll[:-1],roll+b'\x00']:
    try: decode_roll(data)
    except (RuntimeError,ValueError): pass
    else: raise AssertionError('Bad RFID payload accepted')
print('PASS: RFID variable-length fields and truncation checks')

async def check_fragmented_send():
    class Char: max_write_without_response_size=20
    class Client:
        def __init__(self): self.writes=[]
        async def write_gatt_char(self,char,data,response):
            assert response is False; self.writes.append(data)
    c=Connection(None); c.char=Char(); c.client=Client()
    c.queue.put_nowait((0xf1,b'RF\x01\x00'))
    assert await c.command(0xf0,refill_payload(uid),0xf1)==b'RF\x01\x00'
    assert list(map(len,c.client.writes))==[20,3]
    assert b''.join(c.client.writes)==raw
asyncio.run(check_fragmented_send())
print('PASS: reset packet split at 20-byte BLE write boundary without loss or duplicate command')
