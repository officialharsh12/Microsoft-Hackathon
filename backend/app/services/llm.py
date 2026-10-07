import json
from typing import Any, Dict, List, Optional

import requests

from app.config import settings


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class GroundedLLM:
    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or settings.LLM_PROVIDER or "azure-openai").lower()
        self.model = settings.LLM_MODEL or "gpt-4o-mini"
        self.api_key = settings.LLM_API_KEY or ""
        self.endpoint = settings.AZURE_OPENAI_ENDPOINT or ""

    def should_use_provider(self) -> bool:
        return bool(self.api_key) and (self.provider in {"azure-openai", "openai"})

    def build_prompt(self, issue: Dict[str, Any], metrics: Dict[str, Any], evidence: List[Dict[str, Any]]) -> str:
        evidence_lines = []
        for row in evidence[:3]:
            evidence_lines.append(
                f"- Review {row.get('original_id') or row.get('id')}: {row.get('text') or row.get('cleaned_text') or ''}"
            )
        evidence_block = "\n".join(evidence_lines) if evidence_lines else "- No evidence available"

        metric_lines = []
        for key, value in sorted(metrics.items()):
            metric_lines.append(f"- {key}: {value}")
        metric_block = "\n".join(metric_lines) if metric_lines else "- No metric references provided"

        return (
            "You are a PM assistant. Use only the structured facts below. "
            "Do not invent metrics, reviews, or evidence. Label hypotheses clearly as 'Possible Cause', 'Hypothesis', or 'Requires Investigation'.\n\n"
            f"Issue: {issue.get('title') or issue.get('theme') or 'Issue'}\n"
            f"Dataset facts:\n{metric_block}\n\n"
            "Evidence:\n"
            f"{evidence_block}\n\n"
            "Return JSON with keys: summary, possible_causes, recommended_actions, confidence, evidence_review_ids."
        )

    def generate(self, issue: Dict[str, Any], metrics: Dict[str, Any], evidence: List[Dict[str, Any]], fallback: bool = True) -> Dict[str, Any]:
        evidence_review_ids = [
            row.get("id") if row.get("id") is not None else row.get("review_id")
            for row in evidence[:10]
            if row.get("id") is not None or row.get("review_id") is not None
        ]

        if not self.should_use_provider():
            summary = (
                f"{issue.get('title') or issue.get('theme') or 'Issue'} is grounded in dataset metrics and evidence. "
                f"Severity is {metrics.get('severity', 'unavailable')} and the issue trend is {metrics.get('trend', 'unavailable')}. "
                "This analysis does not claim causation without additional investigation."
            )
            return {
                "summary": summary,
                "possible_causes": [
                    {
                        "label": "Possible Cause",
                        "text": "Review evidence suggests a recurring feature or workflow problem. Follow the issue's evidence trail before making a product claim.",
                    }
                ],
                "recommended_actions": [
                    "Review the top evidence entries for customer reports.",
                    "Verify the root cause with product telemetry and engineering logs.",
                ],
                "confidence": "grounded",
                "evidence_review_ids": evidence_review_ids,
                "model_name": "rule-based-grounded-summary",
                "model_version": "1.0",
            }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a PM-focused analysis assistant. Follow evidence-grounded recommendations only.",
                },
                {"role": "user", "content": self.build_prompt(issue, metrics, evidence)},
            ],
            "temperature": 0.2,
        }

        try:
            headers = {
                "Content-Type": "application/json",
                "api-key": self.api_key,
            }
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            body = response.json()
            content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
            try:
                parsed = json.loads(content)
            except Exception:
                parsed = {"summary": content.strip()}
            parsed.setdefault("summary", "Grounded issue summary")
            parsed.setdefault("evidence_review_ids", evidence_review_ids)
            parsed.setdefault("model_name", self.model)
            parsed.setdefault("model_version", "azure-openai")
            return parsed
        except Exception:
            if fallback:
                return self.generate(issue, metrics, evidence, fallback=False)
            return {
                "summary": "LLM fallback unavailable; structured metrics and evidence remain the source of truth.",
                "possible_causes": [{"label": "Requires Investigation", "text": "No external LLM was available. Investigate with telemetry and issue evidence."}],
                "recommended_actions": ["Validate with customer evidence and product telemetry."],
                "confidence": "grounded",
                "evidence_review_ids": evidence_review_ids,
                "model_name": "rule-based-grounded-summary",
                "model_version": "1.0",
            }


def generate_grounded_issue_summary(issue: Dict[str, Any], metrics: Dict[str, Any], evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
    provider = GroundedLLM()
    return provider.generate(issue, metrics, evidence)
