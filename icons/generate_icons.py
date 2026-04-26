#!/usr/bin/env python3
"""Generate icon files for FotoDerp (Windows .ico + macOS .icns source).

Pure Python — no external dependencies. Generates:
  - icons/icon.png   (512x512, PNG) — source for macOS .icns
  - icons/icon.ico   (Windows icon)
"""

import struct
import zlib
import os


def create_png(width, height, pixels):
    """Create a minimal valid PNG from raw RGBA pixels."""
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack('>I', len(data)) + chunk_type + data + crc

    signature = b'\x89PNG\r\n\x1a\n'
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)  # 8-bit RGBA
    ihdr = chunk(b'IHDR', ihdr_data)

    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'  # filter: none
        for x in range(width):
            idx = (y * width + x) * 4
            r, g, b, a = pixels[idx:idx+4]
            raw_data += struct.pack('BBBB', r, g, b, a)

    compressed = zlib.compress(raw_data)
    idat = chunk(b'IDAT', compressed)
    iend = chunk(b'IEND', b'')

    return signature + ihdr + idat + iend



def generate_gradient_icon(size=512):
    """Generate a gradient-based camera icon."""
    pixels = []
    cx, cy = size // 2, size // 2

    for y in range(size):
        for x in range(size):
            dx = (x - cx) / cx
            dy = (y - cy) / cy
            dist = (dx*dx + dy*dy) ** 0.5

            # Background gradient (dark blue to deep navy)
            t = min(dist * 1.2, 1.0)
            r = int(26 + t * (-10))
            g = int(26 + t * (-15))
            b = int(46 + t * (10))

            # Camera body (rounded rectangle shape)
            margin = size * 0.22
            cam_left = margin
            cam_right = size - margin
            cam_top = size * 0.28
            cam_bottom = size * 0.78
            cam_hump_w = size * 0.35
            cam_hump_h = size * 0.12

            in_body = (cam_left <= x <= cam_right and
                       cam_top <= y <= cam_bottom)

            # Hump on top
            hump_center_x = cx
            hump_left = hump_center_x - cam_hump_w // 2
            hump_right = hump_center_x + cam_hump_w // 2
            in_hump = (hump_left <= x <= hump_right and
                       (cam_top - cam_hump_h) <= y <= cam_top)

            # Lens circle
            lens_r = size * 0.12
            lens_dx = x - cx
            lens_dy = y - cy
            in_lens = (lens_dx*lens_dx + lens_dy*lens_dy) <= (lens_r * lens_r)

            # Inner lens ring
            inner_r = size * 0.07
            in_inner = (lens_dx*lens_dx + lens_dy*lens_dy) <= (inner_r * inner_r)

            # Flash dot
            flash_x = cam_right - size * 0.08
            flash_y = cam_top + size * 0.05
            flash_r = size * 0.025
            in_flash = ((x - flash_x)**2 + (y - flash_y)**2) <= (flash_r**2)

            if in_lens:
                r, g, b = 30, 30, 50
            elif in_inner:
                r, g, b = 80, 80, 120
            elif in_body or in_hump:
                r = min(r + 40, 233)
                g = min(g + 40, 69)
                b = min(b + 40, 96)
            elif in_flash:
                r, g, b = 233, 69, 96

            # Edge anti-aliasing (simple)
            alpha = 255
            if not (in_body or in_hump or in_lens or in_inner or in_flash):
                edge_dist = min(
                    abs(x - cam_left), abs(x - cam_right),
                    abs(y - cam_top), abs(y - cam_bottom),
                )
                if edge_dist < 3:
                    alpha = int(edge_dist / 3 * 255)

            pixels.extend([r, g, b, alpha])

    return pixels


def main():
    icon_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(icon_dir)

    print("Generating FotoDerp icons...")

    # Generate 512x512 gradient icon
    pixels = generate_gradient_icon(512)
    png_data = create_png(512, 512, pixels)

    # Write PNG (macOS .icns source)
    with open('icon.png', 'wb') as f:
        f.write(png_data)
    print("Created icon.png (512x512)")

    # Generate ICO
    # Write a proper multi-resolution ICO
    png_sizes = [16, 32, 48, 64, 128, 256]
    pngs = []
    for sz in png_sizes:
        small_pixels = generate_gradient_icon(sz)
        png_bytes = create_png(sz, sz, small_pixels)
        pngs.append((sz, png_bytes))

    # ICO file format
    with open('icon.ico', 'wb') as f:
        # Header: reserved(2), type(2)=ICO, count(2)
        f.write(struct.pack('<HHH', 0, 1, len(pngs)))
        
        offsets = []
        for i, (sz, png_bytes) in enumerate(pngs):
            offset = f.tell() + 16  # entry is 16 bytes
            offsets.append(offset)
            
            w = sz if sz < 256 else 0
            h = sz if sz < 256 else 0
            
            # Directory entry
            f.write(struct.pack('<BBBBHHII',
                               sz if sz < 256 else 0,
                               sz if sz < 256 else 0,
                               0, 0,
                               1, 1,
                               len(png_bytes), offset))
        
        for _, png_bytes in pngs:
            f.write(png_bytes)

    print(f"Created icon.ico ({len(pngs)} resolutions)")
    print("Done!")


if __name__ == '__main__':
    main()
