from __future__ import annotations

import re
from collections.abc import Iterable


_LEGAL_TERMS = (
    "劳动合同",
    "劳动关系",
    "劳动报酬",
    "拖欠工资",
    "拖欠劳动报酬",
    "工资流水",
    "工资条",
    "未签",
    "未签合同",
    "未订立书面劳动合同",
    "二倍工资",
    "违法解除",
    "解除劳动合同",
    "赔偿金",
    "经济补偿",
    "加班费",
    "加班工资",
    "仲裁时效",
    "举证责任",
    "考勤记录",
    "微信聊天",
    "离职证明",
    "关联企业",
    "混同用工",
)

_STOP_CHARS = set("，。！？、；：（）()[]【】《》“”\"' \t\r\n")


def tokenize(text: str) -> list[str]:
    normalized = text.lower().strip()
    tokens: list[str] = []

    for term in _LEGAL_TERMS:
        if term.lower() in normalized:
            tokens.append(term.lower())

    tokens.extend(re.findall(r"[a-z0-9_]+", normalized))

    chinese_chars = [char for char in normalized if "\u4e00" <= char <= "\u9fff"]
    tokens.extend(
        "".join(pair)
        for pair in zip(chinese_chars, chinese_chars[1:], strict=False)
        if not any(char in _STOP_CHARS for char in pair)
    )
    return [token for token in tokens if token and token not in _STOP_CHARS]


def keyword_overlap_score(query: str, text: str) -> float:
    query_tokens = set(tokenize(query))
    if not query_tokens:
        return 0.0
    text_tokens = set(tokenize(text))
    overlap = len(query_tokens.intersection(text_tokens))
    return overlap / max(len(query_tokens), 1)


def stable_embedding(text: str, dimension: int = 64) -> list[float]:
    vector = [0.0] * dimension
    for token in tokenize(text):
        value = _stable_hash(token)
        index = value % dimension
        sign = 1.0 if (value >> 7) % 2 == 0 else -1.0
        vector[index] += sign

    norm = sum(item * item for item in vector) ** 0.5
    if norm == 0:
        return vector
    return [item / norm for item in vector]


def joined_text(parts: Iterable[str | None]) -> str:
    return "\n".join(part.strip() for part in parts if part and part.strip())


def _stable_hash(value: str) -> int:
    result = 2166136261
    for byte in value.encode("utf-8"):
        result ^= byte
        result = (result * 16777619) & 0xFFFFFFFF
    return result
