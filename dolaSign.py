import struct
import hashlib
import time


DEFAULT_KEY_LEN  = 0
DEFAULT_HEAP_PTR = 0


def _b9f3a(key_len: int, heap_char_data_ptr: int) -> bytes:
    return bytes([
        0x4a,
        key_len & 0xff,
        0x16,
        (heap_char_data_ptr >> 8) & 0xff,
        0x47,
        0x6c,
        (key_len >> 8) & 0xff,
        heap_char_data_ptr & 0xff,
    ])


def _e2c71(key_buf: bytes) -> list:
    S = list(range(256))
    j = 0
    key_len = len(key_buf)
    for i in range(256):
        j = (j + S[i] + key_buf[i % key_len]) % 256
        S[i] = S[j]
    return S


def _f8d04(S: list, data: bytes) -> bytes:
    result = bytearray()
    i = j = 0
    S = list(S)
    for byte in data:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        sj = S[j]
        S[i] = sj
        k = S[(sj + sj) % 256]
        result.append(byte ^ k)
    return bytes(result)


def _a1e6b(b: int) -> int:
    return int(f'{b:08b}'[::-1], 2)


def _c4d82(buf: bytes) -> bytes:
    orig = list(buf)
    n = len(orig)
    result = bytearray(n)
    for i in range(n):
        ns = ((orig[i] & 0xf) << 4) | ((orig[i] >> 4) & 0xf)
        if i + 1 < n:
            val = (ns ^ orig[i + 1]) & 0xff
        elif n > 1:
            val = (ns ^ result[0]) & 0xff
        else:
            val = ns
        rbit = _a1e6b(val)
        result[i] = (n ^ (~rbit & 0xff)) & 0xff
    return bytes(result)


def _d7f19(plain20: bytes, key_len: int, heap_char_data_ptr: int) -> bytes:
    assert len(plain20) == 20
    key8 = _b9f3a(key_len, heap_char_data_ptr)
    S = _e2c71(key8)
    encrypted = _f8d04(S, plain20)
    transformed = _c4d82(encrypted)
    header = bytes([
        0x84,
        0x04,
        heap_char_data_ptr & 0xff,
        (heap_char_data_ptr >> 8) & 0xff,
        key_len & 0xff,
        (key_len >> 8) & 0xff,
    ])
    return header + transformed


FLAGS = bytes.fromhex('00050904')


def _b3e90(
    signing_string: str,
    timestamp: int,
    request_context_bytes: bytes = b'\x00\x00\x00\x00',
) -> bytes:
    h = hashlib.md5(signing_string.encode()).digest()[:4]
    ts_bytes = struct.pack('>I', timestamp & 0xffffffff)
    plain = h + request_context_bytes[:4] + b'\x00\x00\x00\x00' + FLAGS + ts_bytes
    assert len(plain) == 20
    return plain


def _f1c53(
    signing_string: str,
    timestamp: int,
    key_len: int = DEFAULT_KEY_LEN,
    heap_char_data_ptr: int = DEFAULT_HEAP_PTR,
    request_context_bytes: bytes = b'\x00\x00\x00\x00',
) -> str:
    plain = _b3e90(signing_string, timestamp, request_context_bytes)
    block = _d7f19(plain, key_len, heap_char_data_ptr)
    return block.hex()


SESSION_FIXED = '7OdAQJLu50UcXnEAwvWduFxCCYujlcj1U5wViru05cv8wZXd'


def sign(
    url: str,
    body: bytes = b'',
    timestamp: int = None,
    key_len: int = DEFAULT_KEY_LEN,
    heap_char_data_ptr: int = DEFAULT_HEAP_PTR,
    request_context_bytes: bytes = b'\x00\x00\x00\x00',
) -> dict:
    if timestamp is None:
        timestamp = int(time.time())
    signing_string = url.split('?', 1)[1] if '?' in url else ''
    return {
        'X-Gorgon':  _f1c53(signing_string, timestamp, key_len,
                             heap_char_data_ptr, request_context_bytes),
        'X-Khronos': str(timestamp),
        'X-Ladon':   SESSION_FIXED,
    }
