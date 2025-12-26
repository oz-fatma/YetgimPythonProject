import os
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk, ImageOps

from constants import (
    INSTAGRAM_SIZE, PREVIEW_MAX, FILTERS, TEXT_POSITIONS, CHROMA_GREEN
)
from image_pipeline import (
    make_instagram_square, apply_filter, apply_adjustments,
    apply_glow, apply_film_grain, apply_text_effect
)
from turtle_underline import (
    turtle_underline_overlay, pil_underline_overlay, hex_to_rgb
)


class InstagramPostMaker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Instagram Post Hazırlayıcı (Tkinter + Yazı Efekti)")
        self.geometry("980x840")
        self.minsize(880, 720)

        self.original_img = None
        self.base_square = None
        self.output_img = None
        self.preview_tk = None

        self._underline_cache_key = None
        self._underline_overlay_cached = None

        self.filter_var = tk.StringVar(value="Normal")
        self.brightness_var = tk.DoubleVar(value=1.0)
        self.contrast_var   = tk.DoubleVar(value=1.0)
        self.saturation_var = tk.DoubleVar(value=1.0)
        self.sharpness_var  = tk.DoubleVar(value=1.0)

        self.glow_on = tk.BooleanVar(value=True)
        self.glow_strength_var = tk.DoubleVar(value=0.35)
        self.glow_radius_var   = tk.DoubleVar(value=6.0)

        self.grain_on = tk.BooleanVar(value=True)
        self.grain_amount_var = tk.DoubleVar(value=0.08)

        self.text_on = tk.BooleanVar(value=True)
        self.text_var = tk.StringVar(value="Merhaba 🌿")
        self.text_pos_var = tk.StringVar(value="Alt-Orta")
        self.text_size_var = tk.IntVar(value=72)
        self.text_color_var = tk.StringVar(value="#FFFFFF")

        self.underline_on = tk.BooleanVar(value=True)
        self.underline_color_var = tk.StringVar(value="#FFFFFF")
        self.underline_thickness_var = tk.IntVar(value=10)
        self.underline_seed_var = tk.IntVar(value=7)

        self._build_ui()
        self.canvas.bind("<Configure>", self._refresh_preview)

    def _build_ui(self):
        top = tk.Frame(self)
        top.pack(fill="x", padx=12, pady=12)

        tk.Button(top, text="📷 Fotoğraf Seç", command=self.pick_image, height=2).pack(side="left")
        tk.Button(top, text="💾 1080x1080 Kaydet", command=self.save_output, height=2).pack(side="left", padx=10)

        self.info = tk.Label(top, text="Seçilen: -", anchor="w")
        self.info.pack(side="left", padx=10)

        self.canvas = tk.Canvas(self, bg="#111", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        controls = tk.Frame(self)
        controls.pack(fill="x", padx=12, pady=(0, 10))

        tk.Label(controls, text="Filtre:").grid(row=0, column=0, sticky="w")
        opt = tk.OptionMenu(controls, self.filter_var, *FILTERS, command=lambda _: self.update_output())
        opt.config(width=14)
        opt.grid(row=0, column=1, sticky="w", padx=(6, 18))

        def slider(row, col, text, var, frm, to, res, length=220):
            tk.Label(controls, text=text).grid(row=row, column=col, sticky="w")
            s = tk.Scale(
                controls, from_=frm, to=to, resolution=res,
                orient="horizontal", length=length, variable=var,
                command=lambda _v: self.update_output()
            )
            s.grid(row=row, column=col+1, sticky="w", padx=(6, 18))
            return s

        slider(0, 2, "Parlaklık", self.brightness_var, 0.5, 1.8, 0.05)
        slider(0, 4, "Kontrast",   self.contrast_var,   0.5, 1.8, 0.05)
        slider(1, 2, "Doygunluk",  self.saturation_var, 0.0, 2.0, 0.05)
        slider(1, 4, "Keskinlik",  self.sharpness_var,  0.0, 2.5, 0.05)

        tk.Button(controls, text="♻️ Sıfırla", command=self.reset_adjustments).grid(row=1, column=1, sticky="w")

        tk.Checkbutton(controls, text="✨ Glow", variable=self.glow_on, command=self.update_output)\
            .grid(row=2, column=0, sticky="w")
        slider(2, 2, "Glow Gücü", self.glow_strength_var, 0.0, 1.0, 0.02)
        slider(2, 4, "Blur Radius", self.glow_radius_var, 0.0, 20.0, 0.5)

        tk.Checkbutton(controls, text="🎞️ Film Grain", variable=self.grain_on, command=self.update_output)\
            .grid(row=3, column=0, sticky="w")
        slider(3, 2, "Grain Yoğunluğu", self.grain_amount_var, 0.0, 0.30, 0.01)

        
        r = 4
        tk.Checkbutton(controls, text="🅰️ Yazı", variable=self.text_on, command=self._invalidate_underline_and_update)\
            .grid(row=r, column=0, sticky="w", pady=(10, 0))

        tk.Entry(controls, textvariable=self.text_var, width=30).grid(
            row=r, column=1, sticky="w", padx=(6, 18), pady=(10, 0)
        )
        self.text_var.trace_add("write", lambda *_: self._invalidate_underline_and_update())

        tk.Label(controls, text="Konum:").grid(row=r, column=2, sticky="w", pady=(10, 0))
        pos = tk.OptionMenu(controls, self.text_pos_var, *TEXT_POSITIONS,
                            command=lambda *_: self._invalidate_underline_and_update())
        pos.config(width=10)
        pos.grid(row=r, column=3, sticky="w", padx=(6, 18), pady=(10, 0))

        tk.Label(controls, text="Boyut").grid(row=r, column=4, sticky="w", pady=(10, 0))
        tk.Scale(
            controls, from_=24, to=140, resolution=2, orient="horizontal", length=220,
            variable=self.text_size_var, command=lambda _v: self._invalidate_underline_and_update()
        ).grid(row=r, column=5, sticky="w", padx=(6, 18), pady=(10, 0))

        r = 5
        tk.Label(controls, text="Yazı Rengi (#RRGGBB):").grid(row=r, column=0, sticky="w")
        tk.Entry(controls, textvariable=self.text_color_var, width=12)\
            .grid(row=r, column=1, sticky="w", padx=(6, 18))

        tk.Checkbutton(controls, text="✍️ Turtle Underline", variable=self.underline_on,
                       command=self._invalidate_underline_and_update)\
            .grid(row=r, column=2, sticky="w")

        tk.Label(controls, text="Renk:").grid(row=r, column=3, sticky="w")
        tk.Entry(controls, textvariable=self.underline_color_var, width=10)\
            .grid(row=r, column=4, sticky="w", padx=(6, 18))

        r = 6
        tk.Label(controls, text="Kalınlık").grid(row=r, column=0, sticky="w")
        tk.Scale(
            controls, from_=2, to=30, resolution=1, orient="horizontal", length=220,
            variable=self.underline_thickness_var, command=lambda _v: self._invalidate_underline_and_update()
        ).grid(row=r, column=1, sticky="w", padx=(6, 18))

        tk.Label(controls, text="Seed").grid(row=r, column=2, sticky="w")
        tk.Entry(controls, textvariable=self.underline_seed_var, width=8)\
            .grid(row=r, column=3, sticky="w", padx=(6, 18))

        tk.Button(controls, text="🔄 Underline Yenile", command=self._invalidate_underline_and_update)\
            .grid(row=r, column=4, sticky="w")

        bottom = tk.Frame(self)
        bottom.pack(fill="x", padx=12, pady=(0, 12))
        tk.Label(bottom, text="1080×1080 — Filtre/efekt + yazı + turtle underline (opsiyonel).").pack(anchor="w")

    def reset_adjustments(self):
        self.filter_var.set("Normal")
        self.brightness_var.set(1.0)
        self.contrast_var.set(1.0)
        self.saturation_var.set(1.0)
        self.sharpness_var.set(1.0)

        self.glow_on.set(True)
        self.glow_strength_var.set(0.35)
        self.glow_radius_var.set(6.0)

        self.grain_on.set(True)
        self.grain_amount_var.set(0.08)

        self._invalidate_underline_and_update()

    def _invalidate_underline_and_update(self):
        self._underline_cache_key = None
        self._underline_overlay_cached = None
        self.update_output()

    def pick_image(self):
        path = filedialog.askopenfilename(
            title="Fotoğraf seç",
            filetypes=[("Görseller", "*.png *.jpg *.jpeg *.webp *.bmp"), ("Tümü", "*.*")]
        )
        if not path:
            return

        try:
            img = Image.open(path)
            img = ImageOps.exif_transpose(img)
            self.original_img = img

            self.base_square = make_instagram_square(img, size=INSTAGRAM_SIZE)
            self._invalidate_underline_and_update()

            fname = os.path.basename(path)
            self.info.config(text=f"Seçilen: {fname}  |  Orijinal: {img.size[0]}×{img.size[1]}")
        except Exception as e:
            messagebox.showerror("Hata", f"Görsel açılamadı:\n{e}")

    def _underline_overlay_provider(self, text_bbox):
        try:
            color_rgb = hex_to_rgb(self.underline_color_var.get())
        except Exception:
            color_rgb = (255, 255, 255)

        thickness = int(self.underline_thickness_var.get())
        seed = int(self.underline_seed_var.get())
        key = (text_bbox, color_rgb, thickness, seed)

        if self._underline_cache_key == key and self._underline_overlay_cached is not None:
            return self._underline_overlay_cached

        x, y, tw, th = text_bbox
        pad_x = int(max(24, tw * 0.06))
        x0 = x - pad_x
        x1 = x + tw + pad_x
        base_y = y + th + 18

        try:
            overlay = turtle_underline_overlay(
                size=INSTAGRAM_SIZE,
                text_bbox=text_bbox,
                stroke_rgb=color_rgb,
                thickness=thickness,
                seed=seed,
                chroma_green=CHROMA_GREEN
            )
        except Exception:
            overlay = pil_underline_overlay(
                size=INSTAGRAM_SIZE,
                x0=x0, x1=x1, y=base_y,
                stroke_rgb=color_rgb,
                thickness=thickness
            )

        self._underline_cache_key = key
        self._underline_overlay_cached = overlay
        return overlay

    def update_output(self):
        if self.base_square is None:
            return

        img = self.base_square.copy()
        img = apply_filter(img, self.filter_var.get())
        img = apply_adjustments(
            img,
            brightness=self.brightness_var.get(),
            contrast=self.contrast_var.get(),
            saturation=self.saturation_var.get(),
            sharpness=self.sharpness_var.get(),
        )
        img = apply_glow(img, self.glow_on.get(), self.glow_strength_var.get(), self.glow_radius_var.get())
        img = apply_film_grain(img, self.grain_on.get(), self.grain_amount_var.get())

        try:
            text_color = hex_to_rgb(self.text_color_var.get())
        except Exception:
            text_color = (255, 255, 255)

        img = apply_text_effect(
            img_rgb=img,
            enabled=self.text_on.get(),
            text=self.text_var.get(),
            text_pos=self.text_pos_var.get(),
            text_size=self.text_size_var.get(),
            text_color_rgb=text_color,
            underline_enabled=self.underline_on.get(),
            underline_overlay_provider=(self._underline_overlay_provider if self.underline_on.get() else None),
        )

        self.output_img = img
        self.show_preview(self.output_img)

    def show_preview(self, img: Image.Image):
        if img is None:
            return
        cw = max(1, self.canvas.winfo_width())
        ch = max(1, self.canvas.winfo_height())
        max_w = min(PREVIEW_MAX, cw)
        max_h = min(PREVIEW_MAX, ch)

        preview = img.copy()
        preview.thumbnail((max_w, max_h), Image.LANCZOS)

        self.preview_tk = ImageTk.PhotoImage(preview)
        self.canvas.delete("all")
        self.canvas.create_image(cw // 2, ch // 2, image=self.preview_tk, anchor="center")

    def _refresh_preview(self, _event=None):
        if self.output_img is not None:
            self.show_preview(self.output_img)

    def save_output(self):
        if self.output_img is None:
            messagebox.showwarning("Uyarı", "Önce bir fotoğraf seçmelisin.")
            return

        path = filedialog.asksaveasfilename(
            title="Kaydet",
            defaultextension=".jpg",
            filetypes=[("JPEG", "*.jpg *.jpeg"), ("PNG", "*.png"), ("Tümü", "*.*")]
        )
        if not path:
            return

        try:
            img_to_save = self.output_img
            if path.lower().endswith((".jpg", ".jpeg")) and img_to_save.mode != "RGB":
                img_to_save = img_to_save.convert("RGB")

            if path.lower().endswith((".jpg", ".jpeg")):
                img_to_save.save(path, quality=95, optimize=True)
            else:
                img_to_save.save(path)

            messagebox.showinfo("Kaydedildi", f"Kayıt tamam:\n{path}")
        except Exception as e:
            messagebox.showerror("Hata", f"Kaydedilemedi:\n{e}")
