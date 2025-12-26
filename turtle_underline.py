import os
import math
import random
import tempfile
from pathlib import Path

import turtle
from PIL import Image, ImageOps, ImageDraw


def turtle_underline_overlay(
    size: tuple[int, int],
    text_bbox: tuple[int, int, int, int],   # (x, y, tw, th)
    stroke_rgb: tuple[int, int, int],
    thickness: int,
    seed: int,
    chroma_green: tuple[int, int, int] = (0, 255, 0),
) -> Image.Image:
    """
    Turtle ile underline çizip transparan RGBA overlay üretir.
    Ghostscript / PS->Image dönüşümü sorun olursa exception fırlatır (UI fallback kullanır).
    """
    w, h = size
    x, y, tw, th = text_bbox

    pad_x = int(max(24, tw * 0.06))
    x0 = x - pad_x
    x1 = x + tw + pad_x
    base_y = y + th + 18

    def to_turtle(px, py):
        tx = px - (w / 2)
        ty = (h / 2) - py
        return tx, ty

    tmp_dir = Path(tempfile.gettempdir())
    ps_path = tmp_dir / f"underline_{os.getpid()}_{seed}.ps"

    turtle.colormode(255)
    scr = turtle.Screen()
    scr.setup(width=w, height=h)
    scr.bgcolor(chroma_green)
    scr.title("Underline üretiliyor... (otomatik kapanacak)")
    scr.tracer(0, 0)

    t = turtle.Turtle(visible=False)
    t.speed(0)
    t.pensize(int(thickness))
    t.pencolor(int(stroke_rgb[0]), int(stroke_rgb[1]), int(stroke_rgb[2]))
    t.penup()

    rng = random.Random(int(seed))
    steps = 80
    amp = 6 + min(16, int(thickness))
    freq = rng.choice([1.5, 2.0, 2.5])

    sx, sy = to_turtle(x0, base_y)
    t.goto(sx, sy)
    t.pendown()

    for i in range(steps + 1):
        px = x0 + (x1 - x0) * (i / steps)
        wobble = math.sin((i / steps) * math.pi * 2 * freq) * amp
        wobble += rng.uniform(-amp * 0.35, amp * 0.35)
        py = base_y + wobble
        tx, ty = to_turtle(px, py)
        t.goto(tx, ty)

    scr.update()

    cv = scr.getcanvas()
    cv.postscript(file=str(ps_path), colormode="color")
    scr.bye()

    img = Image.open(ps_path).convert("RGB")
    img = ImageOps.fit(img, (w, h), method=Image.LANCZOS, centering=(0.5, 0.5))
    img_rgba = img.convert("RGBA")

    datas = img_rgba.getdata()
    new_data = []
    for r, g, b, a in datas:
        if (r, g, b) == chroma_green:
            new_data.append((0, 0, 0, 0))
        else:
            new_data.append((r, g, b, 255))
    img_rgba.putdata(new_data)

    try:
        ps_path.unlink(missing_ok=True)
    except Exception:
        pass

    return img_rgba


def pil_underline_overlay(
    size: tuple[int, int],
    x0: int,
    x1: int,
    y: int,
    stroke_rgb: tuple[int, int, int],
    thickness: int,
) -> Image.Image:
    w, h = size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    d.line([(x0, y), (x1, y)], fill=(stroke_rgb[0], stroke_rgb[1], stroke_rgb[2], 255), width=int(thickness))
    return overlay


def hex_to_rgb(s: str) -> tuple[int, int, int]:
    s = s.strip()
    if s.startswith("#"):
        s = s[1:]
    if len(s) != 6:
        raise ValueError("Renk #RRGGBB olmalı")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
