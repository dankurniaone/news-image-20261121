#!/usr/bin/env python3
"""Draw the 21 November 2026 front page and write entry.png.

Pillow only. No network, no clock, no randomness: the same news.json
and the same three photographs always produce the same bytes. The page
is composed at double size (1360x2048) and shrunk with LANCZOS to
680x1024 so the small type stays crisp. The three photographs are real
CC-licensed file photos, credited in the README; the masthead, rules
and type are drawn in code. Run from the repo root:

    python3 tools/render21.py
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
FONTS = "/usr/share/fonts/truetype/dejavu"

PAPER = (250, 246, 236)
INK = (20, 20, 18)
GREY = (104, 98, 88)
RED = (178, 34, 34)
HAIR = (200, 192, 176)

S = 2  # render scale
W, H = 680 * S, 1024 * S
MARGIN = 36 * S
BODY = W - 2 * MARGIN


class Fonts:
    def __init__(self):
        self._seen = {}

    def __call__(self, kind, size, bold=False):
        key = (kind, size, bold)
        if key not in self._seen:
            if kind == "serif":
                fname = "DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf"
            else:
                fname = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
            self._seen[key] = ImageFont.truetype(
                os.path.join(FONTS, fname), size)
        return self._seen[key]


class Page:
    def __init__(self, copy):
        self.copy = copy
        self.font = Fonts()
        self.img = Image.new("RGB", (W, H), PAPER)
        self.d = ImageDraw.Draw(self.img)

    def wrap(self, text, font, width):
        lines, cur = [], ""
        for word in text.split():
            trial = word if not cur else cur + " " + word
            if self.d.textlength(trial, font=font) <= width:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines

    def text_block(self, x, y, text, font, fill, width, lead):
        for line in self.wrap(text, font, width):
            self.d.text((x, y), line, font=font, fill=fill)
            y += lead
        return y

    def centre(self, y, text, font, fill):
        w = self.d.textlength(text, font=font)
        self.d.text(((W - w) / 2, y), text, font=font, fill=fill)
        return y + font.size

    def spaced(self, y, text, font, fill, gap):
        ws = [self.d.textlength(ch, font=font) for ch in text]
        total = sum(ws) + gap * (len(text) - 1)
        x = (W - total) / 2
        for ch, w in zip(text, ws):
            self.d.text((x, y), ch, font=font, fill=fill)
            x += w + gap
        return y + font.size

    def rule(self, y, weight=2, fill=INK):
        self.d.line([(MARGIN, y), (W - MARGIN, y)], fill=fill, width=weight)
        return y + weight

    def place_photo(self, name, x, y, w, h):
        src = Image.open(os.path.join(ROOT, "assets", name)).convert("RGB")
        self.img.paste(ImageOps.fit(src, (w, h), Image.LANCZOS), (x, y))
        return y + h

    def masthead(self):
        n = self.copy
        y = 40
        self.d.rectangle([MARGIN, y, W - MARGIN, y + 6], fill=RED)
        y += 22
        y = self.centre(y, n["masthead"], self.font("serif", 108, True), INK)
        y += 6
        y = self.spaced(y, n["masthead_tag"], self.font("sans", 30, True),
                        INK, 14)
        y += 10
        y = self.centre(y, n["date"].upper(), self.font("sans", 28), GREY)
        y += 12
        y = self.rule(y)
        y += 14
        y = self.centre(y, n["strapline"], self.font("serif", 26), GREY)
        return y + 12

    def lead(self, y):
        n = self.copy["lead"]
        self.d.text((MARGIN, y), n["kicker"], font=self.font("sans", 26, True),
                    fill=RED)
        y += 40
        y = self.text_block(MARGIN, y, n["headline"],
                            self.font("serif", 64, True), INK, BODY, 76)
        y += 8
        y = self.text_block(MARGIN, y, n["deck"], self.font("serif", 31),
                            INK, BODY, 42)
        y += 14
        y = self.place_photo("andes.jpg", MARGIN, y, BODY, 372)
        y += 12
        y = self.text_block(MARGIN, y, n["photo_caption"],
                            self.font("sans", 20), GREY, BODY, 26)
        y += 12
        return self.rule(y) + 14

    def columns(self, y):
        gap = 40
        col = (BODY - gap) // 2
        lx, rx = MARGIN, MARGIN + col + gap
        top = y
        ends = []
        for key, photo, x in (("rahul", "cricket_a.jpg", lx),
                              ("cop31", "turbines_b.jpg", rx)):
            s = self.copy[key]
            yy = top
            self.d.text((x, yy), s["kicker"], font=self.font("sans", 26, True),
                        fill=RED)
            yy += 40
            yy = self.text_block(x, yy, s["headline"],
                                 self.font("serif", 36, True), INK, col, 44)
            yy += 8
            yy = self.text_block(x, yy, s["deck"], self.font("serif", 26),
                                 INK, col, 35)
            yy += 14
            yy = self.place_photo(photo, x, yy, col, 226)
            yy += 10
            yy = self.text_block(x, yy, s["photo_caption"],
                                 self.font("sans", 20), GREY, col, 26)
            ends.append(yy)
        self.d.line([(MARGIN + col + gap // 2, top),
                     (MARGIN + col + gap // 2, max(ends))],
                    fill=HAIR, width=2)
        return max(ends) + 16

    def markets(self, y):
        n = self.copy["markets"]
        x = MARGIN + 24
        body = n["headline"] + " — " + n["deck"]
        lines = self.wrap(body, self.font("serif", 26), BODY - 24)
        box = 8 + 32 + len(lines) * 34 + 10
        self.d.rectangle([MARGIN, y, MARGIN + 8, y + box], fill=RED)
        yy = y + 8
        self.d.text((x, yy), n["kicker"], font=self.font("sans", 22, True),
                    fill=RED)
        yy += 32
        for line in lines:
            self.d.text((x, yy), line, font=self.font("serif", 26), fill=INK)
            yy += 34
        return y + box + 16

    def ticker(self, y):
        text = self.copy["ticker"]
        self.d.rectangle([MARGIN, y, W - MARGIN, y + 56], fill=RED)
        size = 25
        f = self.font("sans", size, True)
        w = self.d.textlength(text, font=f)
        while w > BODY - 40 and size > 14:
            size -= 1
            f = self.font("sans", size, True)
            w = self.d.textlength(text, font=f)
        self.d.text(((W - w) / 2, y + (56 - size) // 2 - 2), text, font=f,
                    fill=(255, 255, 255))
        return y + 56 + 10

    def footer(self, y):
        y = self.text_block(MARGIN, y, self.copy["footer"],
                            self.font("sans", 20), GREY, BODY, 26)
        y += 12
        return self.rule(y)

    def build(self):
        y = self.masthead()
        y = self.lead(y)
        y = self.columns(y)
        y = self.markets(y)
        y = self.ticker(y)
        y = self.footer(y)
        assert y <= H - 30, f"page overflow: y={y} of {H}"
        out = self.img.resize((680, 1024), Image.LANCZOS)
        path = os.path.join(ROOT, "entry.png")
        out.save(path, optimize=True)
        print(f"entry.png: {os.path.getsize(path)} bytes")


def main():
    with open(os.path.join(ROOT, "news.json")) as f:
        copy = json.load(f)
    Page(copy).build()


if __name__ == "__main__":
    main()
