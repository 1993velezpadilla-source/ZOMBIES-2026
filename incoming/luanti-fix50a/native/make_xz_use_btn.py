#!/usr/bin/env python3
"""Build the independent USE touch icon with Python stdlib only.
Run from Luanti source root: python3 path/to/make_xz_use_btn.py textures/base/pack/xz_use_btn.png
"""
from pathlib import Path
import struct
import sys
import zlib

N = 128
pixels = bytearray(N * N * 4)

def put(x, y, color):
    if 0 <= x < N and 0 <= y < N:
        pixels[(y*N + x)*4:(y*N + x + 1)*4] = bytes(color)

# Rounded square matching the stock translucent touchscreen controls.
for y in range(N):
    for x in range(N):
        dx = max(abs(x - 63.5) - 43, 0)
        dy = max(abs(y - 63.5) - 43, 0)
        dist = dx*dx + dy*dy
        inside = 8 <= x <= 119 and 8 <= y <= 119 and dist <= 19*19
        border = inside and (x<13 or x>114 or y<13 or y>114 or dist>14*14)
        if inside:
            put(x, y, (245, 248, 252, 250) if border else (20, 30, 40, 214))

letters = {
    'U': ['10001','10001','10001','10001','10001','10001','01110'],
    'S': ['01111','10000','10000','01110','00001','00001','11110'],
    'E': ['11111','10000','10000','11110','10000','10000','11111'],
}
scale = 5
text_width = 5*3*scale + 2*2*scale
left, top = (N-text_width)//2, 46
for pos, char in enumerate('USE'):
    for gy, bits in enumerate(letters[char]):
        for gx, bit in enumerate(bits):
            if bit != '1':
                continue
            for oy in range(scale):
                for ox in range(scale):
                    put(left+(pos*7+gx)*scale+ox, top+gy*scale+oy,
                        (250, 252, 255, 255))

def png_chunk(kind, payload):
    return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind+payload) & 0xffffffff)

raw = b''.join(b'\0' + pixels[y*N*4:(y+1)*N*4] for y in range(N))
image = (b'\x89PNG\r\n\x1a\n' + png_chunk(b'IHDR', struct.pack('>IIBBBBB', N, N, 8, 6, 0, 0, 0))
         + png_chunk(b'IDAT', zlib.compress(raw, 9)) + png_chunk(b'IEND', b''))
out = Path(sys.argv[1] if len(sys.argv)>1 else 'xz_use_btn.png')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_bytes(image)
print(f'{out}: {len(image)} bytes')