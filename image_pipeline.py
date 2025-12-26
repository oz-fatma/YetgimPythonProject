import os
from PIL import (
    Image, ImageOps, ImageEnhance,
    ImageFilter, ImageChops, ImageDraw, ImageFont
)

#Instagram için kare boyutu getir
def make_instagram_square(img: Image.Image, size=(1080, 1080)) -> Image.Image:
    if img.mode == "RGBA":
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img).convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")
    return ImageOps.fit(img, size, method=Image.LANCZOS, centering=(0.5, 0.5))

#Filtre uygula
def apply_filter(img: Image.Image, filter_name: str) -> Image.Image:
    f = filter_name
    if f == "Normal":
        return img
    if f == "Siyah-Beyaz":
        return ImageOps.grayscale(img).convert("RGB")
    if f == "Invert":
        return ImageOps.invert(img)
    if f == "Sepya":
        g = ImageOps.grayscale(img)
        return ImageOps.colorize(g, black="#2b1b0f", white="#f2d7b6").convert("RGB")
    if f == "Sıcak":
        r, g, b = img.split()
        r = r.point(lambda i: min(255, int(i * 1.08)))
        b = b.point(lambda i: max(0, int(i * 0.94)))
        return Image.merge("RGB", (r, g, b))
    if f == "Soğuk":
        r, g, b = img.split()
        b = b.point(lambda i: min(255, int(i * 1.08)))
        r = r.point(lambda i: max(0, int(i * 0.94)))
        return Image.merge("RGB", (r, g, b))
    return img

#Görüntü ayarlarını uygula
def apply_adjustments(img: Image.Image, brightness: float, contrast: float, saturation: float, sharpness: float) -> Image.Image:
    img = ImageEnhance.Brightness(img).enhance(float(brightness))
    img = ImageEnhance.Contrast(img).enhance(float(contrast))
    img = ImageEnhance.Color(img).enhance(float(saturation))
    img = ImageEnhance.Sharpness(img).enhance(float(sharpness))
    return img

#Parlama efekti uygulama
def apply_glow(img: Image.Image, enabled: bool, strength: float, radius: float) -> Image.Image:
    if not enabled:
        return img
    strength = float(strength)
    radius = float(radius)
    if strength <= 0.0 or radius <= 0.0:
        return img
    blurred = img.filter(ImageFilter.GaussianBlur(radius=radius))
    screened = ImageChops.screen(img, blurred)
    return Image.blend(img, screened, strength)

#Film grain efekti uygula
def apply_film_grain(img: Image.Image, enabled: bool, amount: float) -> Image.Image:
    if not enabled:
        return img
    amount = float(amount)
    if amount <= 0.0:
        return img
    w, h = img.size
    sigma = 5 + int(amount * 180)
    noise = Image.effect_noise((w, h), sigma).convert("RGB")
    noise = noise.filter(ImageFilter.GaussianBlur(radius=0.6))
    return Image.blend(img, noise, amount)

#Metin fontlarını al
def get_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Helvetica.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size=int(size))
            except Exception:
                pass
    return ImageFont.load_default()

#Metin pozisyonlarını ayarla
def text_xy(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, pos_name: str, canvas_size=(1080, 1080)):
    w, h = canvas_size
    margin = 70
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    x = (w - tw) // 2
    if pos_name == "Üst-Orta":
        y = margin
    elif pos_name == "Orta":
        y = (h - th) // 2
    else:
        y = h - margin - th
    return x, y, tw, th


def apply_text_effect(
    img_rgb: Image.Image,
    enabled: bool,
    text: str,
    text_pos: str,
    text_size: int,
    text_color_rgb: tuple[int, int, int],
    underline_enabled: bool,
    underline_overlay_provider,  # callable(text_bbox)->RGBA overlay or None
) -> Image.Image:
    if not enabled:
        return img_rgb

    text = (text or "").strip()
    if not text:
        return img_rgb

    img = img_rgb.convert("RGBA")
    base = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)

    font = get_font(int(text_size))
    x, y, tw, th = text_xy(draw, text, font, text_pos, canvas_size=img.size)
    text_bbox = (x, y, tw, th)

    if underline_enabled and underline_overlay_provider is not None:
        overlay = underline_overlay_provider(text_bbox)
        if overlay is not None:
            base = Image.alpha_composite(base, overlay)

    # shadow
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 140))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=2.0))
    base = Image.alpha_composite(base, shadow)

    # text
    draw = ImageDraw.Draw(base)
    r, g, b = text_color_rgb
    draw.text((x, y), text, font=font, fill=(int(r), int(g), int(b), 255))

    out = Image.alpha_composite(img, base).convert("RGB")
    return out
