from __future__ import annotations

import re


# Chuẩn hóa tên tác giả một cách bảo toàn, không ghi đè dữ liệu gốc
def normalize_author(author: str | None) -> str | None:
    if author is None:
        return None
    value = re.sub(r"\s+", " ", str(author)).strip()
    value = re.sub(r"\s*\(\s*Tổng hợp\s*\)", " tổng hợp", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", " ", value).strip()
    return value or None
