#!/usr/bin/env python3
"""Generate the Argus logo SVGs (icon, lockup, social banner). Stdlib only.

    python3 assets/build_logo.py

The mark is a pixel-block eye (Argus Panoptes, the hundred-eyed watcher) with a few
small "other eyes" around it, built from plain rectangles so it needs no fonts.
"""
from pathlib import Path

BG = "#151713"
LIME = "#C1FF00"
SHADOW = "#5C7A00"

META = (
    '<metadata><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:cc="http://creativecommons.org/ns#">'
    '<rdf:Description rdf:about=""><dc:creator>Arda Kaan Özcan</dc:creator>'
    '<dc:rights>© 2026 Arda Kaan Özcan. MIT License.</dc:rights>'
    '<dc:source>https://github.com/ardakaano/argus</dc:source>'
    '<cc:attributionName>Arda Kaan Özcan</cc:attributionName></rdf:Description></rdf:RDF></metadata>'
)

# Almond eye, 15 columns x 9 rows: (first_col, last_col) per row.
EYE_ROWS = [(5, 9), (3, 11), (1, 13), (0, 14), (0, 14), (0, 14), (1, 13), (3, 11), (5, 9)]
PUPIL = (6, 3, 3, 3)       # col, row, width, height in cells
GLINT = (6, 3)             # lime cell inside the pupil
DOTS = [(-1, -3), (3, -4), (8, -3), (12, -4), (15, -2), (0, 11), (5, 12), (10, 11), (14, 12)]  # other eyes

FONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "G": [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
}


def rect(x, y, w, h, fill, extra=""):
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{fill}"{extra}/>'


def eye(x, y, cell, shadow):
    """Pixel eye with its top-left corner at (x, y). Returns SVG elements."""
    out = []
    for dx, dy, color in ((shadow, shadow, SHADOW), (0, 0, LIME)):
        if dx:
            out.append(f'<g transform="translate({dx:g} {dy:g})">')
        for row, (a, b) in enumerate(EYE_ROWS):
            out.append(rect(x + a * cell, y + row * cell, (b - a + 1) * cell, cell, color))
        if dx:
            out.append('</g>')
    pc, pr, pw, ph = PUPIL
    out.append(rect(x + pc * cell, y + pr * cell, pw * cell, ph * cell, BG))
    out.append(rect(x + GLINT[0] * cell, y + GLINT[1] * cell, cell, cell, LIME))
    return out


def dots(x, y, cell):
    return [rect(x + c * cell, y + r * cell, cell, cell, LIME, ' opacity=".55"') for c, r in DOTS]


def word(x, y, cell, text="ARGUS"):
    out = []
    for dx, dy, color in ((cell / 2, cell / 2, SHADOW), (0, 0, LIME)):
        for i, ch in enumerate(text):
            for r, line in enumerate(FONT[ch]):
                c = 0
                while c < 5:
                    if line[c] == "#":
                        start = c
                        while c < 5 and line[c] == "#":
                            c += 1
                        out.append(rect(x + dx + (i * 6 + start) * cell, y + dy + r * cell, (c - start) * cell, cell, color))
                    else:
                        c += 1
    return out


def svg(width, height, body, title, rounded=0):
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" '
            f'height="{height}" role="img" aria-label="{title}">\n{META}\n<title>{title}</title>\n')
    plate = rect(0, 0, width, height, BG, f' rx="{rounded}"' if rounded else "")
    return head + plate + "\n" + "\n".join(body) + "\n</svg>\n"


def main():
    out = Path(__file__).resolve().parent

    # Square icon: 15x9 eye at cell 4 on a 72x72 plate.
    cell = 4
    icon = dots(6, 18, cell) + eye(6, 18, cell, 2)
    (out / "icon.svg").write_text(svg(72, 72, icon, "Argus", rounded=14), encoding="utf-8")

    # Horizontal lockup: eye + ARGUS wordmark.
    ec, wc = 6, 6
    pad, gap = 40, 36
    eye_w, eye_h = 15 * ec, 9 * ec
    word_w, word_h = (5 * 6 - 1) * wc, 7 * wc
    width = pad * 2 + eye_w + gap + word_w
    height = pad * 2 + eye_h + 2 * 4 * ec
    ey = (height - eye_h) // 2
    body = dots(pad, ey, ec) + eye(pad, ey, ec, 3) + word(pad + eye_w + gap, (height - word_h) / 2, wc)
    (out / "logo.svg").write_text(svg(width, height, body, "Argus", rounded=18), encoding="utf-8")

    # Social preview, 1280x640: big mark, wordmark, tagline.
    w, h = 1280, 640
    ec = 16
    mark_w = 15 * ec
    wc = 14
    text_w = (5 * 6 - 1) * wc
    mark_x, word_x = (w - mark_w) // 2, (w - text_w) // 2
    body = dots(mark_x, 96, ec)
    body += eye(mark_x, 96, ec, 6)
    body += word(word_x, 96 + 9 * ec + 96, wc)
    body.append(f'<text x="{w // 2}" y="{h - 70}" text-anchor="middle" fill="{LIME}" opacity=".85" '
                'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="28" '
                'letter-spacing="3">A HUNDRED EYES ON YOUR LAUNCH</text>')
    (out / "social-preview.svg").write_text(svg(w, h, body, "Argus: a hundred eyes on your launch"), encoding="utf-8")


if __name__ == "__main__":
    main()
