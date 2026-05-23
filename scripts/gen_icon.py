"""Download a weird emoji PNG and scale it to 512x512 for Tauri icon."""
import os
import struct
import zlib
import urllib.request

URL = "https://raw.githubusercontent.com/twitter/twemoji/master/assets/72x72/1f4a9.png"
SIZE = 512

def read_png(data):
    """Read raw RGBA pixels from PNG data using stdlib only."""
    pos = 8  # skip signature
    raw_pixels = b''
    width = height = 0
    while pos < len(data):
        length = struct.unpack('>I', data[pos:pos+4])[0]
        ctype = data[pos+4:pos+8]
        if ctype == b'IHDR':
            width, height = struct.unpack('>II', data[pos+8:pos+16])
        elif ctype == b'IDAT':
            raw_pixels += data[pos+8:pos+8+length]
        elif ctype == b'IEND':
            break
        pos += 12 + length
    return width, height, zlib.decompress(raw_pixels)

def write_png(width, height, pixels):
    """Write RGBA pixels to PNG bytes."""
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)

    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    raw = b''
    for y in range(height):
        raw += b'\x00'  # filter none
        for x in range(width):
            raw += pixels[(y * width + x) * 4:(y * width + x) * 4 + 4]
    idat = zlib.compress(raw)

    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b'')

def nearest_scale(src_w, src_h, src_pixels, dst_w, dst_h):
    """Nearest-neighbor scale RGBA pixels."""
    dst = bytearray(dst_w * dst_h * 4)
    for dy in range(dst_h):
        sy = dy * src_h // dst_h
        for dx in range(dst_w):
            sx = dx * src_w // dst_w
            si = (sy * src_w + sx) * 4
            di = (dy * dst_w + dx) * 4
            dst[di:di+4] = src_pixels[si:si+4]
    return bytes(dst)

if __name__ == '__main__':
    icon_path = os.path.join('frontend', 'src-tauri', 'icons', 'icon.png')
    os.makedirs(os.path.dirname(icon_path), exist_ok=True)

    print(f'Downloading poop emoji...')
    try:
        req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
        src_data = urllib.request.urlopen(req, timeout=30).read()
        sw, sh, src_pixels = read_png(src_data)
        print(f'Read {sw}x{sh} PNG, scaling to {SIZE}x{SIZE}...')
        scaled = nearest_scale(sw, sh, src_pixels, SIZE, SIZE)
        png = write_png(SIZE, SIZE, scaled)
    except Exception as e:
        print(f'Download failed ({e}), generating fallback pattern...')
        PX = 16
        png_data = b''
        for y in range(SIZE):
            png_data += b'\x00'
            for x in range(SIZE):
                bx, by = x // PX, y // PX
                if (bx + by) % 3 == 0:
                    png_data += b'\xe7\x4c\x3c\xff'
                elif (bx + by) % 3 == 1:
                    png_data += b'\x34\x98\xdb\xff'
                else:
                    png_data += b'\xf3\x9c\x12\xff'
        png = write_png(SIZE, SIZE, png_data)

    with open(icon_path, 'wb') as f:
        f.write(png)
    print(f'Icon saved to {icon_path} ({len(png)} bytes)')
