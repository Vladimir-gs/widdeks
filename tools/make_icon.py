"""Genera el icono de Widdeks (.ico multi-resolución + PNG de marca).

Uso:
    python tools/make_icon.py
"""

import os

from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "clock-widget", "assets")
SIZES = (16, 24, 32, 48, 64, 128, 256)
SS = 8  # supersampling

BG = (30, 30, 36, 255)
BORDER = (255, 255, 255, 55)
INK = (236, 236, 244, 255)
ACCENT = (128, 226, 150, 255)


def render(size):
    s = size * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    pad = int(s * 0.03)
    radius = int(s * 0.22)
    d.rounded_rectangle(
        [pad, pad, s - pad - 1, s - pad - 1],
        radius=radius,
        fill=BG,
        outline=BORDER,
        width=max(1, int(s * 0.012)),
    )

    face_pad = int(s * 0.20)
    lw = max(2, int(s * 0.055))
    d.ellipse(
        [face_pad, face_pad, s - face_pad - 1, s - face_pad - 1],
        outline=INK,
        width=lw,
    )

    cx = cy = s / 2
    w = max(2, int(s * 0.045))
    hand_v = int(s * 0.17)
    hand_h = int(s * 0.13)

    # Manecillas con puntas redondeadas.
    d.line([cx, cy, cx, cy - hand_v], fill=INK, width=w)
    d.ellipse([cx - w / 2, cy - hand_v - w / 2, cx + w / 2, cy - hand_v + w / 2], fill=INK)
    d.line([cx, cy, cx + hand_h, cy], fill=INK, width=w)
    d.ellipse([cx + hand_h - w / 2, cy - w / 2, cx + hand_h + w / 2, cy + w / 2], fill=INK)

    dot = max(2, int(s * 0.035))
    d.ellipse([cx - dot, cy - dot, cx + dot, cy + dot], fill=ACCENT)

    return img.resize((size, size), Image.LANCZOS)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    master = render(256)
    ico_path = os.path.join(OUT_DIR, "widdeks.ico")
    master.save(ico_path, format="ICO", sizes=[(n, n) for n in SIZES])
    print(f"ICO: {ico_path}")

    png_path = os.path.join(OUT_DIR, "widdeks.png")
    render(512).save(png_path)
    print(f"PNG: {png_path}")


if __name__ == "__main__":
    main()
