"""QR 解碼與內容分類；所有處理均在本機完成。"""

from __future__ import annotations

from urllib.parse import urlparse

import cv2
import numpy as np
import zxingcpp


WEB_SCHEMES = {"http", "https"}
APP_SCHEMES = {"line"}


def is_openable_url(value: str) -> bool:
    """Only treat explicit http(s) or LINE protocol URLs as openable."""
    parsed = urlparse(value.strip())
    if parsed.scheme.lower() in WEB_SCHEMES:
        return bool(parsed.netloc)
    if parsed.scheme.lower() in APP_SCHEMES:
        return bool(parsed.netloc or parsed.path)
    return False


def decode_qr_png(png_bytes: bytes) -> list[str]:
    """Decode QR codes from a selected screen image, entirely on-device.

    ZXing-C++ handles small, anti-aliased, and tightly cropped QR images more
    reliably than OpenCV alone. OpenCV remains as a local fallback.
    """
    source = np.frombuffer(png_bytes, dtype=np.uint8)
    image = cv2.imdecode(source, cv2.IMREAD_COLOR)
    if image is None:
        return []

    values: list[str] = []

    # A selection often excludes the QR code's quiet zone. Recreate one before
    # decoding and enlarge small screen captures without blurring their cells.
    grayscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _threshold, binary = cv2.threshold(grayscale, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    variants = (image, grayscale, binary)
    for variant in variants:
        height, width = variant.shape[:2]
        border = max(16, min(height, width) // 8)
        padded = cv2.copyMakeBorder(variant, border, border, border, border, cv2.BORDER_CONSTANT, value=255)
        minimum = min(padded.shape[:2])
        if minimum < 720:
            scale = 720 / minimum
            padded = cv2.resize(padded, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
        try:
            results = zxingcpp.read_barcodes(padded, formats=zxingcpp.BarcodeFormat.QRCode, try_rotate=True, try_downscale=False)
            values.extend(result.text.strip() for result in results if result.text and result.text.strip())
        except (RuntimeError, ValueError):
            pass

    # Retain OpenCV as a no-network fallback for unusual QR variations.
    if not values:
        detector = cv2.QRCodeDetector()
        try:
            detected, decoded, _points, _straight = detector.detectAndDecodeMulti(image)
            if detected:
                values.extend(value.strip() for value in decoded if value and value.strip())
        except cv2.error:
            pass

        if not values:
            try:
                value, _points, _straight = detector.detectAndDecode(image)
                if value and value.strip():
                    values.append(value.strip())
            except cv2.error:
                pass

    # A duplicate QR in an image should still be treated as one result.
    return list(dict.fromkeys(values))
