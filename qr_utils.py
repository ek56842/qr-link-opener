"""QR 解碼與內容分類；所有處理均在本機完成。"""

from __future__ import annotations

from urllib.parse import urlparse

import cv2
import numpy as np


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
    """Decode all QR codes contained in a PNG byte string."""
    source = np.frombuffer(png_bytes, dtype=np.uint8)
    image = cv2.imdecode(source, cv2.IMREAD_COLOR)
    if image is None:
        return []

    detector = cv2.QRCodeDetector()
    values: list[str] = []
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
