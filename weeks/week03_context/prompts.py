"""Three prompt versions. Extra tokens must buy measurable accuracy, not vibes."""

from __future__ import annotations

from dataclasses import dataclass

from weeks.week02_classifier.classify import SYSTEM_PROMPT as BASELINE_PROMPT


@dataclass(frozen=True)
class PromptVersion:
    name: str
    system: str


COMPACT = PromptVersion(
    name="compact",
    system=(
        "Classify one support ticket into the JSON schema. "
        "Use only ticket evidence. Low confidence => needs_human true."
    ),
)

BASELINE = PromptVersion(name="baseline", system=BASELINE_PROMPT)

FEW_SHOT = PromptVersion(
    name="few_shot",
    system=BASELINE_PROMPT
    + """

Field rules:
- intent=bug: HTTP 5xx, 502, site down, export crash, production outage
- intent=billing: invoice, duplicate charge, refund
- intent=feature: a new capability request, not a how-to question
- intent=question: asking how a product/plan works
- intent=account: login, password, access
- intent=complaint: agent/process attitude
- intent=other: too vague to act
- priority=critical: whole production down; high: money/outage/complaint; else low/medium

Examples (paraphrased, not eval tickets):
1) "CSV export returns 500, customers waiting" -> intent=bug, priority=high, needs_human=true
2) "Please add Slack webhooks, not a bug" -> intent=feature, priority=low, needs_human=false
3) "Hi, I will ask later" -> intent=other, confidence<=0.2, needs_human=true
4) "What's the difference between Solo and Business plans?" -> intent=question, priority=low, needs_human=false
""",
)

VERSIONS = {item.name: item for item in (COMPACT, BASELINE, FEW_SHOT)}
