"""Generate a 512x512 ProAgent icon PNG using stdlib only."""
import os
import struct
import zlib

SIZE = 512

# ProAgent brand colors (blue gradient)
BG_R, BG_G, BG_B = 0x34, 0x98, 0xDB
ACCENT_R, ACCENT_G, ACCENT_B = 0xE7, 0x4C, 0x3C


def create_icon():
    raw = b''
    cx, cy, radius = SIZE // 2, SIZE // 2, SIZE // 3

    for y in range(SIZE):
        raw += b'\x00'  # filter: None
        for x in range(SIZE):
            dx, dy = x - cx, y - cy
            dist = (dx * dx + dy * dy) ** 0.5

            if dist < radius:
                # Inner circle: accent color
                raw += bytes([ACCENT_R, ACCENT_G, ACCENT_B, 0xFF])
            elif dist < radius + 8:
                # Border
                raw += bytes([0xFF, 0xFF, 0xFF, 0xFF])
            else:
                # Background
                raw += bytes([BG_R, BG_G, BG_B, 0xFF])

    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = struct.pack('>IIBBBBB', SIZE, SIZE, 8, 6, 0, 0, 0)
    idat = zlib.compress(raw)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')


if __name__ == '__main__':
    icon_dir = os.path.join('frontend', 'src-tauri', 'icons')
    os.makedirs(icon_dir, exist_ok=True)
    icon_path = os.path.join(icon_dir, 'icon.png')

    png = create_icon()
    with open(icon_path, 'wb') as f:
        f.write(png)

    print(f'Icon saved to {icon_path} ({len(png)} bytes)')
