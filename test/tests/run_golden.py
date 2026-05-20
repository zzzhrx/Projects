"""Golden test runner for the business travel agent framework.

Runs deterministic pipeline checks (routing, slot extraction, recommendation)
against a JSON case file. Does NOT require LLM or network access.
"""

from __future__ import annotations

import sys
from dataclasses import fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json

from agent_framework.agent.service import AdvancedAgentService
from agent_framework.core.models import AgentRequest
from agent_framework.domains.business_travel import (
    analyze_travel_brief,
    build_travel_context,
    build_travel_recommendation,
)
from agent_framework.routing.default import KeywordSkillRouter
from agent_framework.skills.defaults import build_default_skill_registry


def load_cases() -> list[dict[str, Any]]:
    cases_path = Path(__file__).resolve().parent / "golden" / "cases.json"
    with open(cases_path, encoding="utf-8") as f:
        data = json.load(f)
    return data or []


def run_routing_and_extraction(case: dict[str, Any]) -> dict[str, Any]:
    inp = case["input"]
    query = inp["query"]
    thread_id = inp.get("thread_id", "golden-test")

    skill_registry = build_default_skill_registry()
    router = KeywordSkillRouter()

    context: dict[str, Any] = {"current_date": inp.get("current_date", "2026-05-20")}
    for hist in inp.get("history", []):
        hist_query = hist["query"]
        hist_skill = hist["skill"]
        context = build_travel_context(hist_query, context)
        context["_last_skill"] = hist_skill

    decision = router.route(query, skill_registry, context)

    assessment = analyze_travel_brief(query, context)

    recommendation_fields: list[str] = []
    if assessment.readiness.startswith("ready"):
        rec = build_travel_recommendation(assessment.brief, assessment)
        recommendation_fields = [f.name for f in fields(rec)]

    result: dict[str, Any] = {
        "skill": decision.skill.name,
        "confidence": decision.confidence,
        "reason": decision.reason,
        "readiness": assessment.readiness,
        "brief_fields": {
            "origin": assessment.brief.origin,
            "destination": assessment.brief.destination,
            "departure_date": assessment.brief.departure_date,
            "departure_date_iso": assessment.brief.departure_date_iso,
            "arrival_deadline": assessment.brief.arrival_deadline,
            "return_date": assessment.brief.return_date,
            "return_date_iso": assessment.brief.return_date_iso,
            "budget_policy": assessment.brief.budget_policy,
            "transport_preference": assessment.brief.transport_preference,
            "business_location": assessment.brief.business_location,
            "hotel_area": assessment.brief.hotel_area,
            "notes": assessment.brief.notes,
        },
        "missing_keys": list(assessment.missing_keys),
        "recommendation_keys": recommendation_fields,
    }
    return result


def check_expectations(case: dict[str, Any], result: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    expect = case.get("expect", {})

    if "skill" in expect:
        if result["skill"] != expect["skill"]:
            failures.append(
                f"skill: expected {expect['skill']!r}, got {result['skill']!r}"
            )

    if "min_confidence" in expect:
        if result["confidence"] < expect["min_confidence"]:
            failures.append(
                f"confidence: expected >= {expect['min_confidence']}, got {result['confidence']:.2f}"
            )

    if "brief_fields" in expect:
        for key, expected_val in expect["brief_fields"].items():
            actual = result["brief_fields"].get(key)
            if expected_val != actual:
                failures.append(
                    f"brief.{key}: expected {expected_val!r}, got {actual!r}"
                )

    if "readiness" in expect:
        if result["readiness"] != expect["readiness"]:
            failures.append(
                f"readiness: expected {expect['readiness']!r}, got {result['readiness']!r}"
            )

    if "recommendation_keys" in expect:
        missing_keys = set(expect["recommendation_keys"]) - set(result["recommendation_keys"])
        if missing_keys:
            failures.append(
                f"recommendation missing keys: {sorted(missing_keys)} (have: {sorted(result['recommendation_keys'])})"
            )

    return failures


def main() -> int:
    cases = load_cases()
    if not cases:
        print("No golden cases found.")
        return 1

    passed = 0
    failed = 0
    for case in cases:
        case_id = case["id"]
        description = case.get("description", "")
        try:
            result = run_routing_and_extraction(case)
            failures = check_expectations(case, result)
        except Exception as exc:
            print(f"  FAIL  {case_id}: {description}")
            print(f"         Error: {exc}")
            failed += 1
            continue

        if failures:
            print(f"  FAIL  {case_id}: {description}")
            for f in failures:
                print(f"         {f}")
            failed += 1
        else:
            print(f"  PASS  {case_id}: {description}")
            passed += 1

    print(f"\n{passed} passed, {failed} failed, {len(cases)} total")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
