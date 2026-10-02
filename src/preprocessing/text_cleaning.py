from __future__ import annotations

import re
import unicodedata

_WHITESPACE_RE = re.compile(r"\s+")
_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)


# Chuẩn hóa văn bản tiếng Việt sang dạng Unicode NFC
def normalize_unicode(text: str | None) -> str:
    return unicodedata.normalize("NFC", str(text)) if text else ""


# Loại bỏ URL và quy chuẩn khoảng trắng nhưng giữ nguyên dấu câu
def normalize_text(text: str | None) -> str:
    text = normalize_unicode(text)
    text = _URL_RE.sub(" ", text)
    text = text.replace("\u00a0", " ")
    return _WHITESPACE_RE.sub(" ", text).strip()


# Tách từ cơ bản dựa trên khoảng trắng
def tokenize(text: str | None) -> list[str]:
    cleaned = normalize_text(text)
    return cleaned.split() if cleaned else []


# Đếm số lượng câu dựa trên dấu kết thúc câu (.!?…)
def sentence_count(text: str | None) -> int:
    cleaned = normalize_text(text)
    if not cleaned:
        return 0
    return sum(bool(p.strip()) for p in re.split(r"(?<=[.!?…])\s+", cleaned))


# Loại bỏ đoạn mở đầu trùng lặp với tiêu đề hoặc mô tả do quá trình bóc tách HTML
def remove_leading_duplicate_blocks(content: str | None, title: str | None = None, description: str | None = None) -> str:
    value, title_n, desc_n = normalize_text(content), normalize_text(title), normalize_text(description)
    if not value:
        return ""
    if title_n:
        while value.startswith(title_n + " "):
            value = value[len(title_n):].lstrip()
    if desc_n and value.startswith(desc_n + " "):
        value = value[len(desc_n):].lstrip()
    return value


# Tính toán các chỉ số đặc trưng từ vựng cơ bản của chuỗi văn bản
def lexical_features(text: str | None) -> dict[str, float | int]:
    cleaned = normalize_text(text)
    tokens = tokenize(cleaned)
    lengths = [len(re.sub(r"[^\wÀ-ỹĐđ]", "", t, flags=re.UNICODE)) for t in tokens]
    lengths = [n for n in lengths if n > 0]
    unique = {t.casefold() for t in tokens}
    return {
        "char_count": len(cleaned),
        "word_count": len(tokens),
        "sentence_count": sentence_count(cleaned),
        "unique_word_count": len(unique),
        "lexical_diversity": round(len(unique) / len(tokens), 6) if tokens else 0.0,
        "avg_word_length": round(sum(lengths) / len(lengths), 6) if lengths else 0.0,
    }
