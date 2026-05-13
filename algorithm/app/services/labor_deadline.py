from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class DeadlineRisk:
    name: str
    due_date: date | None
    risk_level: str
    message: str


class LaborDeadlineService:
    """Rule placeholder for labor arbitration limitation periods."""

    def assess_arbitration_limitation(
        self,
        dispute_known_at: date | None,
        today: date | None = None,
    ) -> DeadlineRisk:
        if dispute_known_at is None:
            return DeadlineRisk(
                name="劳动仲裁时效",
                due_date=None,
                risk_level="unknown",
                message="缺少争议发生或知道权利受侵害的日期，需补充后判断时效风险。",
            )

        current = today or date.today()
        due_date = dispute_known_at + timedelta(days=365)
        remaining_days = (due_date - current).days
        if remaining_days < 0:
            level = "high"
            message = "可能已经超过一年劳动仲裁时效，需结合中断、中止等事实复核。"
        elif remaining_days <= 30:
            level = "medium"
            message = "距离一年劳动仲裁时效较近，建议尽快准备材料。"
        else:
            level = "low"
            message = "目前未发现明显临近时效风险，仍需结合具体日期复核。"

        return DeadlineRisk(
            name="劳动仲裁时效",
            due_date=due_date,
            risk_level=level,
            message=message,
        )
