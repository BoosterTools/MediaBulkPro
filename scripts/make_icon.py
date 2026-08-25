"""Generate the MediaBulk Pro icon (play button + download arrow motif)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "assets" / "icons"
SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
<rect width="256" height="256" rx="56" fill="#4F46E5"/>
<circle cx="128" cy="108" r="62" fill="#FFFFFF"/>
<path d="M110 82l48 26-48 26z" fill="#4F46E5"/>
<path d="M128 150v46m0 0l-20-20m20 20l20-20" stroke="#FFFFFF" stroke-width="12"
 stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>"""


def draw(size: int) -> Image.Image:
    s = size / 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=int(56 * s), fill="#4F46E5")
    d.ellipse((66 * s, 46 * s, 190 * s, 170 * s), fill="#FFFFFF")
    d.polygon([(110 * s, 82 * s), (158 * s, 108 * s), (110 * s, 134 * s)], fill="#4F46E5")
    d.line([(128 * s, 150 * s), (128 * s, 196 * s)], fill="#FFFFFF", width=max(2, int(12 * s)))
    d.line([(108 * s, 176 * s), (128 * s, 196 * s)], fill="#FFFFFF", width=max(2, int(12 * s)))
    d.line([(148 * s, 176 * s), (128 * s, 196 * s)], fill="#FFFFFF", width=max(2, int(12 * s)))
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "mediabulk.svg").write_text(SVG, encoding="utf-8")
    base = draw(256)
    base.save(OUT / "mediabulk.png")
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    base.save(OUT / "mediabulk.ico", sizes=sizes)
    print("icons written to", OUT)


if __name__ == "__main__":
    main()
