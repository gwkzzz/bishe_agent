from __future__ import annotations

from dataclasses import dataclass


BLOCKED_PATTERNS = (
    "伪造证据",
    "补做证据",
    "威胁对方",
    "逃避执行",
)

RISKY_CERTAINTY_PATTERNS = (
    "一定能胜诉",
    "一定会支持",
    "保证没问题",
)


@dataclass(frozen=True)
class SafetyReviewResult:
    allowed: bool
    rewritten_text: str
    risk_flags: list[str]


class SafetyPolicyService:
    def review_text(self, text: str) -> SafetyReviewResult:
        risk_flags: list[str] = []
        allowed = True
        rewritten = text

        for pattern in BLOCKED_PATTERNS:
            if pattern in rewritten:
                allowed = False
                risk_flags.append(f"blocked:{pattern}")

        for pattern in RISKY_CERTAINTY_PATTERNS:
            if pattern in rewritten:
                risk_flags.append(f"certainty:{pattern}")
                rewritten = rewritten.replace(pattern, "需要结合证据和程序进一步判断")

        return SafetyReviewResult(
            allowed=allowed,
            rewritten_text=rewritten,
            risk_flags=risk_flags,
        )
