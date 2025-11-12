from __future__ import annotations

from io import BytesIO
from typing import List

from PIL import Image, ImageOps


def create_thumbnail(image_bytes: bytes, size: int = 300) -> bytes:
    with Image.open(BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        fitted = ImageOps.fit(img, (size, size), method=Image.Resampling.LANCZOS)
        buffer = BytesIO()
        fitted.save(buffer, format="JPEG", quality=90)
        return buffer.getvalue()


def extract_dominant_colors(image_bytes: bytes, top_n: int = 3) -> List[str]:
    with Image.open(BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        palette_base = img.resize((200, 200))
        quantized = palette_base.quantize(colors=top_n, method=Image.MEDIANCUT)
        palette = quantized.getpalette()
        color_counts = sorted(quantized.getcolors() or [], reverse=True)
        colors = []
        for _, palette_index in color_counts[:top_n]:
            base_index = palette_index * 3
            r, g, b = palette[base_index : base_index + 3]
            colors.append(f"#{r:02x}{g:02x}{b:02x}")
        return colors

