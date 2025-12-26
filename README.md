# Instagram Post Hazırlayıcı (Tkinter + Pillow)

Bu uygulama, bilgisayarından bir fotoğraf seçip onu Instagram post formatına (**1080×1080, 1:1**) otomatik merkezden kırpar.  
Canlı önizleme ile filtre/ayarlar uygulayıp çıktıyı JPG/PNG olarak kaydedebilirsin.

> Projede opsiyonel **Turtle underline** (yazı altı el çizimi çizgi) özelliği vardır. Turtle çıktısını görsele dönüştürmek için macOS’ta çoğu zaman **Ghostscript** gerekir.

---

## Ekran Görüntüsü

![Uygulama Önizleme](assets/screenshot-main.png)

---

## Özellikler

- 1.Fotoğraf seçme (JPG/PNG/WEBP/BMP)
- 2.Otomatik merkezden kırpma + 1080×1080’e ölçekleme
- 3.Ayarlar:
  - Parlaklık
  - Kontrast
  - Doygunluk
  - Keskinlik
- 4.Glow efekti (blur + screen blend)
- 5.Film grain (noise) efekti
- 6.Yazı ekleme (konum, boyut, renk)
- 7.(Opsiyonel) Turtle underline: yazının altına el çizimi gibi dalgalı çizgi (seed ile aynı çizgiyi tekrar üretme)
- 8.Canlı önizleme (pencere büyüyünce otomatik yeniden ortalar)
- 9.JPG/PNG olarak kaydetme

---

## Proje Yapısı
instagram_post_maker/
main.py
ui_app.py
image_pipeline.py
turtle_underline.py
constants.py
requirements.txt
assets/
screenshot-main.png
