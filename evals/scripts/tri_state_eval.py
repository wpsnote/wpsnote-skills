#!/usr/bin/env python3
"""Outcome-only tri-state eval validator and grader."""

from __future__ import annotations

import argparse
import json
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

REQUIRED_CASE_FIELDS = {
    "id",
    "skill",
    "prompt",
    "seed",
    "original_state_collectors",
    "expected_state",
    "final_state_collectors",
    "grader",
    "cleanup",
}

REQUIRED_EXPECTED_STATE_FIELDS = {
    "entities_expected_created",
    "entities_expected_updated",
    "entities_expected_unchanged",
    "required_changes",
    "forbidden_changes",
    "tolerance_rules",
}

SUPPORTED_ASSERTION_KINDS = {
    "path_exists",
    "path_missing",
    "path_changed",
    "path_unchanged",
    "value_equals",
    "value_contains",
    "value_contains_all",
    "value_not_contains",
    "count_equals",
    "count_at_least",
    "count_between",
    "set_equals",
    "regex_matches",
}

SUPPORTED_TOLERANCE_KINDS = {"ignore_paths"}

MISSING = object()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(data: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def iter_case_files(inputs: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for path in inputs:
        if path.is_dir():
            files.extend(sorted(path.rglob("*.json")))
        else:
            files.append(path)
    return files


def validate_case(case: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    missing_fields = REQUIRED_CASE_FIELDS - set(case.keys())
    if missing_fields:
        errors.append(f"缺少顶层字段: {', '.join(sorted(missing_fields))}")

    expected_state = case.get("expected_state")
    if not isinstance(expected_state, dict):
        errors.append("expected_state 必须是对象")
    else:
        missing_expected = REQUIRED_EXPECTED_STATE_FIELDS - set(expected_state.keys())
        if missing_expected:
            errors.append(
                f"expected_state 缺少字段: {', '.join(sorted(missing_expected))}"
            )

        for field in (
            "entities_expected_created",
            "entities_expected_updated",
            "entities_expected_unchanged",
        ):
            value = expected_state.get(field)
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                errors.append(f"expected_state.{field} 必须是字符串数组")

        for field in ("required_changes", "forbidden_changes"):
            value = expected_state.get(field)
            if not isinstance(value, list):
                errors.append(f"expected_state.{field} 必须是数组")
                continue
            for index, rule in enumerate(value):
                errors.extend(validate_assertion(rule, f"expected_state.{field}[{index}]"))

        tolerance_rules = expected_state.get("tolerance_rules")
        if not isinstance(tolerance_rules, list):
            errors.append("expected_state.tolerance_rules 必须是数组")
        else:
            for index, rule in enumerate(tolerance_rules):
                errors.extend(
                    validate_tolerance_rule(rule, f"expected_state.tolerance_rules[{index}]")
                )

    for field in ("original_state_collectors", "final_state_collectors"):
        collectors = case.get(field)
        if not isinstance(collectors, list):
            errors.append(f"{field} 必须是数组")
            continue
        for index, collector in enumerate(collectors):
            if not isinstance(collector, dict):
                errors.append(f"{field}[{index}] 必须是对象")
                continue
            if not isinstance(collector.get("id"), str) or not collector["id"].strip():
                errors.append(f"{field}[{index}] 缺少有效 id")
            if not isinstance(collector.get("kind"), str) or not collector["kind"].strip():
                errors.append(f"{field}[{index}] 缺少有效 kind")

    return errors


def validate_assertion(rule: Any, prefix: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(rule, dict):
        return [f"{prefix} 必须是对象"]

    kind = rule.get("kind")
    path = rule.get("path")
    if kind not in SUPPORTED_ASSERTION_KINDS:
        errors.append(f"{prefix}.kind 不受支持: {kind}")
    if not isinstance(path, str) or not path.strip():
        errors.append(f"{prefix}.path 必须是非空字符串")

    if kind in {"value_equals", "value_contains", "value_not_contains", "count_equals", "count_at_least", "set_equals"}:
        if "value" not in rule:
            errors.append(f"{prefix} 需要 value")

    if kind == "value_contains_all" and not isinstance(rule.get("values"), list):
        errors.append(f"{prefix} 需要 values 数组")

    if kind == "count_between":
        if "min" not in rule or "max" not in rule:
            errors.append(f"{prefix} 需要 min 和 max")

    if kind == "regex_matches" and not isinstance(rule.get("pattern"), str):
        errors.append(f"{prefix} 需要 pattern")

    return errors


def validate_tolerance_rule(rule: Any, prefix: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(rule, dict):
        return [f"{prefix} 必须是对象"]

    kind = rule.get("kind")
    paths = rule.get("paths")
    if kind not in SUPPORTED_TOLERANCE_KINDS:
        errors.append(f"{prefix}.kind 不受支持: {kind}")
    if not isinstance(paths, list) or any(not isinstance(path, str) for path in paths):
        errors.append(f"{prefix}.paths 必须是字符串数组")
    return errors


def tokenize_path(path: str) -> list[str | int]:
    tokens: list[str | int] = []
    current = ""
    i = 0
    while i < len(path):
        char = path[i]
        if char == ".":
            if current:
                tokens.append(current)
                current = ""
            i += 1
            continue
        if char == "[":
            if current:
                tokens.append(current)
                current = ""
            end = path.find("]", i)
            if end == -1:
                raise ValueError(f"无效路径: {path}")
            index_str = path[i + 1:end]
            if not index_str.isdigit():
                raise ValueError(f"无效列表索引: {path}")
            tokens.append(int(index_str))
            i = end + 1
            continue
        current += char
        i += 1
    if current:
        tokens.append(current)
    return tokens


def format_child_path(base: str, child: str | int) -> str:
    if isinstance(child, int):
        return f"{base}[{child}]" if base else f"[{child}]"
    return f"{base}.{child}" if base else child


def path_exists(data: Any, path: str) -> bool:
    value = get_path(data, path, default=MISSING)
    return value is not MISSING


def get_path(data: Any, path: str, default: Any = MISSING) -> Any:
    current = data
    try:
        for token in tokenize_path(path):
            if isinstance(token, int):
                if not isinstance(current, list) or token >= len(current):
                    return default
                current = current[token]
            else:
                if not isinstance(current, dict) or token not in current:
                    return default
                current = current[token]
        return current
    except ValueError:
        return default


def should_ignore(path: str, ignored_paths: set[str]) -> bool:
    for ignored in ignored_paths:
        if path == ignored:
            return True
        if ignored and path.startswith(f"{ignored}."):
            return True
        if ignored and path.startswith(f"{ignored}["):
            return True
    return False


def normalize_value(value: Any, base_path: str, ignored_paths: set[str]) -> Any:
    if should_ignore(base_path, ignored_paths):
        return MISSING

    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, child in value.items():
            child_path = format_child_path(base_path, key)
            normalized_child = normalize_value(child, child_path, ignored_paths)
            if normalized_child is not MISSING:
                normalized[key] = normalized_child
        return normalized

    if isinstance(value, list):
        normalized_list: list[Any] = []
        for index, child in enumerate(value):
            child_path = format_child_path(base_path, index)
            normalized_child = normalize_value(child, child_path, ignored_paths)
            if normalized_child is not MISSING:
                normalized_list.append(normalized_child)
        return normalized_list

    return value


def truncate_preview(value: Any, limit: int = 160) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def diff_states(
    original: Any,
    final: Any,
    base_path: str = "",
    ignored_paths: set[str] | None = None,
    max_entries: int = 50,
) -> list[dict[str, Any]]:
    ignored_paths = ignored_paths or set()
    changes: list[dict[str, Any]] = []

    def walk(before: Any, after: Any, path: str) -> None:
        if len(changes) >= max_entries:
            return
        if should_ignore(path, ignored_paths):
            return

        if isinstance(before, dict) and isinstance(after, dict):
            for key in sorted(set(before) | set(after)):
                child_path = format_child_path(path, key)
                before_value = before.get(key, MISSING)
                after_value = after.get(key, MISSING)
                if before_value is MISSING:
                    changes.append(
                        {
                            "path": child_path,
                            "change_type": "added",
                            "after": truncate_preview(after_value),
                        }
                    )
                    if len(changes) >= max_entries:
                        return
                    continue
                if after_value is MISSING:
                    changes.append(
                        {
                            "path": child_path,
                            "change_type": "removed",
                            "before": truncate_preview(before_value),
                        }
                    )
                    if len(changes) >= max_entries:
                        return
                    continue
                walk(before_value, after_value, child_path)
            return

        if isinstance(before, list) and isinstance(after, list):
            max_len = max(len(before), len(after))
            for index in range(max_len):
                child_path = format_child_path(path, index)
                before_value = before[index] if index < len(before) else MISSING
                after_value = after[index] if index < len(after) else MISSING
                if before_value is MISSING:
                    changes.append(
                        {
                            "path": child_path,
                            "change_type": "added",
                            "after": truncate_preview(after_value),
                        }
                    )
                    if len(changes) >= max_entries:
                        return
                    continue
                if after_value is MISSING:
                    changes.append(
                        {
                            "path": child_path,
                            "change_type": "removed",
                            "before": truncate_preview(before_value),
                        }
                    )
                    if len(changes) >= max_entries:
                        return
                    continue
                walk(before_value, after_value, child_path)
            return

        if before != after:
            changes.append(
                {
                    "path": path or "$",
                    "change_type": "changed",
                    "before": truncate_preview(before),
                    "after": truncate_preview(after),
                }
            )

    walk(original, final, base_path)
    return changes


def summarize_state(state: Any) -> dict[str, Any]:
    if not isinstance(state, dict):
        return {"type": type(state).__name__}

    summary: dict[str, Any] = {
        "top_level_keys": sorted(state.keys()),
        "entity_counts": {},
    }

    for key, value in state.items():
        if isinstance(value, dict):
            summary["entity_counts"][key] = len(value)
            if key == "notes":
                summary["note_ids"] = sorted(value.keys())
            if key == "tags":
                summary["tag_ids"] = sorted(value.keys())
        elif isinstance(value, list):
            summary["entity_counts"][key] = len(value)

    return summary


def summarize_expected(expected_state: dict[str, Any]) -> dict[str, Any]:
    return {
        "entities_expected_created": len(expected_state.get("entities_expected_created", [])),
        "entities_expected_updated": len(expected_state.get("entities_expected_updated", [])),
        "entities_expected_unchanged": len(expected_state.get("entities_expected_unchanged", [])),
        "required_changes": len(expected_state.get("required_changes", [])),
        "forbidden_changes": len(expected_state.get("forbidden_changes", [])),
        "tolerance_rules": len(expected_state.get("tolerance_rules", [])),
    }


def to_count(value: Any) -> int | float:
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, (list, tuple, set, dict, str)):
        return len(value)
    raise TypeError(f"无法计数: {type(value).__name__}")


def contains_value(container: Any, value: Any) -> bool:
    if isinstance(container, str):
        return str(value) in container
    if isinstance(container, dict):
        return value in container or value in container.values()
    if isinstance(container, (list, tuple, set)):
        return value in container
    return False


def changed_between(
    original: Any,
    final: Any,
    path: str,
    ignored_paths: set[str],
) -> bool:
    original_value = get_path(original, path, default=MISSING)
    final_value = get_path(final, path, default=MISSING)
    if original_value is MISSING and final_value is MISSING:
        return False
    if original_value is MISSING or final_value is MISSING:
        return True
    normalized_original = normalize_value(original_value, path, ignored_paths)
    normalized_final = normalize_value(final_value, path, ignored_paths)
    return normalized_original != normalized_final


def evaluate_assertion(
    rule: dict[str, Any],
    original_state: dict[str, Any],
    final_state: dict[str, Any],
    ignored_paths: set[str],
) -> tuple[bool, str]:
    kind = rule["kind"]
    path = rule["path"]

    if kind == "path_exists":
        return path_exists(final_state, path), f"{path} 应存在"

    if kind == "path_missing":
        return not path_exists(final_state, path), f"{path} 应不存在"

    if kind == "path_changed":
        return changed_between(original_state, final_state, path, ignored_paths), f"{path} 应发生变化"

    if kind == "path_unchanged":
        return not changed_between(original_state, final_state, path, ignored_paths), f"{path} 应保持不变"

    value = get_path(final_state, path, default=MISSING)
    if value is MISSING:
        return False, f"{path} 不存在"

    if kind == "value_equals":
        expected = rule["value"]
        return value == expected, f"{path} 应等于 {truncate_preview(expected)}"

    if kind == "value_contains":
        expected = rule["value"]
        return contains_value(value, expected), f"{path} 应包含 {truncate_preview(expected)}"

    if kind == "value_contains_all":
        expected_values = rule.get("values", [])
        return all(contains_value(value, expected) for expected in expected_values), (
            f"{path} 应包含全部值 {truncate_preview(expected_values)}"
        )

    if kind == "value_not_contains":
        expected = rule["value"]
        return not contains_value(value, expected), f"{path} 不应包含 {truncate_preview(expected)}"

    if kind == "count_equals":
        expected = rule["value"]
        actual = to_count(value)
        return actual == expected, f"{path} 计数应等于 {expected}"

    if kind == "count_at_least":
        expected = rule["value"]
        actual = to_count(value)
        return actual >= expected, f"{path} 计数应至少为 {expected}"

    if kind == "count_between":
        minimum = rule["min"]
        maximum = rule["max"]
        actual = to_count(value)
        return minimum <= actual <= maximum, f"{path} 计数应在 {minimum} 到 {maximum} 之间"

    if kind == "set_equals":
        expected = set(rule["value"])
        if isinstance(value, dict):
            actual = set(value.keys())
        else:
            actual = set(value)
        return actual == expected, f"{path} 集合应等于 {truncate_preview(sorted(expected))}"

    if kind == "regex_matches":
        pattern = rule["pattern"]
        return re.search(pattern, str(value)) is not None, f"{path} 应匹配 /{pattern}/"

    raise ValueError(f"不支持的断言 kind: {kind}")


def evaluate_entity_expectations(
    expected_state: dict[str, Any],
    original_state: dict[str, Any],
    final_state: dict[str, Any],
    ignored_paths: set[str],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for path in expected_state.get("entities_expected_created", []):
        passed = not path_exists(original_state, path) and path_exists(final_state, path)
        results.append(
            {
                "kind": "entity_created",
                "path": path,
                "passed": passed,
                "message": f"{path} 应在 final_state 中新增",
            }
        )

    for path in expected_state.get("entities_expected_updated", []):
        passed = path_exists(original_state, path) and path_exists(final_state, path) and changed_between(
            original_state,
            final_state,
            path,
            ignored_paths,
        )
        results.append(
            {
                "kind": "entity_updated",
                "path": path,
                "passed": passed,
                "message": f"{path} 应在 final_state 中被更新",
            }
        )

    for path in expected_state.get("entities_expected_unchanged", []):
        passed = path_exists(original_state, path) and path_exists(final_state, path) and not changed_between(
            original_state,
            final_state,
            path,
            ignored_paths,
        )
        results.append(
            {
                "kind": "entity_unchanged",
                "path": path,
                "passed": passed,
                "message": f"{path} 应保持不变",
            }
        )

    return results


def collect_ignored_paths(expected_state: dict[str, Any]) -> set[str]:
    ignored: set[str] = set()
    for rule in expected_state.get("tolerance_rules", []):
        if rule.get("kind") == "ignore_paths":
            ignored.update(rule.get("paths", []))
    return ignored


def evaluate_rule_group(
    rules: list[dict[str, Any]],
    group_name: str,
    original_state: dict[str, Any],
    final_state: dict[str, Any],
    ignored_paths: set[str],
    negate: bool = False,
) -> tuple[list[dict[str, Any]], list[str]]:
    results: list[dict[str, Any]] = []
    failed_reasons: list[str] = []

    for rule in rules:
        satisfied, default_message = evaluate_assertion(rule, original_state, final_state, ignored_paths)
        passed = not satisfied if negate else satisfied
        detail_message = rule.get("message") or default_message
        result = {
            "label": rule.get("label") or rule["kind"],
            "kind": rule["kind"],
            "path": rule["path"],
            "passed": passed,
            "message": detail_message,
            "mode": "forbidden" if negate else "required",
        }
        results.append(result)

        if not passed:
            prefix = "触发了禁改项" if negate else "未满足必需项"
            failed_reasons.append(f"{prefix}: {detail_message}")

    return results, failed_reasons


def build_report(
    case: dict[str, Any],
    original_state: dict[str, Any],
    final_state: dict[str, Any],
    *,
    bootstrap_error: str | None = None,
    run_error: str | None = None,
) -> dict[str, Any]:
    expected_state = case["expected_state"]
    ignored_paths = collect_ignored_paths(expected_state)

    base_report = {
        "case_id": case["id"],
        "skill": case["skill"],
        "suite": case.get("suite", ""),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }

    if bootstrap_error:
        report = {
            **base_report,
            "status": "bootstrap_fail",
            "checks": {
                "entity_expectations": [],
                "required_changes": [],
                "forbidden_changes": [],
                "tolerance_rules": expected_state.get("tolerance_rules", []),
            },
            "state_diff_report": {
                "original_state_summary": {},
                "expected_state_summary": summarize_expected(expected_state),
                "final_state_summary": {},
                "actual_delta": [],
                "failed_reasons": [bootstrap_error],
            },
        }
        return report

    if run_error:
        report = {
            **base_report,
            "status": "run_fail",
            "checks": {
                "entity_expectations": [],
                "required_changes": [],
                "forbidden_changes": [],
                "tolerance_rules": expected_state.get("tolerance_rules", []),
            },
            "state_diff_report": {
                "original_state_summary": summarize_state(original_state),
                "expected_state_summary": summarize_expected(expected_state),
                "final_state_summary": summarize_state(final_state),
                "actual_delta": [],
                "failed_reasons": [run_error],
            },
        }
        return report

    entity_results = evaluate_entity_expectations(
        expected_state,
        original_state,
        final_state,
        ignored_paths,
    )
    entity_failures = [
        f"实体期望未满足: {result['message']}"
        for result in entity_results
        if not result["passed"]
    ]

    required_results, required_failures = evaluate_rule_group(
        expected_state.get("required_changes", []),
        "required_changes",
        original_state,
        final_state,
        ignored_paths,
        negate=False,
    )
    forbidden_results, forbidden_failures = evaluate_rule_group(
        expected_state.get("forbidden_changes", []),
        "forbidden_changes",
        original_state,
        final_state,
        ignored_paths,
        negate=True,
    )

    failures = entity_failures + required_failures + forbidden_failures
    status = "pass" if not failures else "assert_fail"
    max_diff_entries = int(case.get("grader", {}).get("max_diff_entries", 50))

    report = {
        **base_report,
        "status": status,
        "checks": {
            "entity_expectations": entity_results,
            "required_changes": required_results,
            "forbidden_changes": forbidden_results,
            "tolerance_rules": expected_state.get("tolerance_rules", []),
        },
        "state_diff_report": {
            "original_state_summary": summarize_state(original_state),
            "expected_state_summary": summarize_expected(expected_state),
            "final_state_summary": summarize_state(final_state),
            "actual_delta": diff_states(
                original_state,
                final_state,
                ignored_paths=ignored_paths,
                max_entries=max_diff_entries,
            ),
            "failed_reasons": failures,
        },
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['case_id']}",
        "",
        f"- Skill: `{report['skill']}`",
        f"- Suite: `{report.get('suite') or 'n/a'}`",
        f"- Status: `{report['status']}`",
        "",
        "## State Diff Report",
        "",
        f"- Original: `{json.dumps(report['state_diff_report']['original_state_summary'], ensure_ascii=False)}`",
        f"- Expected: `{json.dumps(report['state_diff_report']['expected_state_summary'], ensure_ascii=False)}`",
        f"- Final: `{json.dumps(report['state_diff_report']['final_state_summary'], ensure_ascii=False)}`",
        "",
        "### Failed Reasons",
    ]

    failed_reasons = report["state_diff_report"]["failed_reasons"]
    if failed_reasons:
        lines.extend(f"- {reason}" for reason in failed_reasons)
    else:
        lines.append("- None")

    lines.extend(["", "### Actual Delta"])
    delta = report["state_diff_report"]["actual_delta"]
    if delta:
        for change in delta:
            lines.append(
                f"- `{change['path']}`: {change['change_type']}"
            )
    else:
        lines.append("- No visible delta")

    return "\n".join(lines) + "\n"


def cmd_validate(args: argparse.Namespace) -> int:
    case_files = iter_case_files([Path(path) for path in args.paths])
    if not case_files:
        print("未找到 case 文件", file=sys.stderr)
        return 1

    has_errors = False
    for path in case_files:
        try:
            case = load_json(path)
        except json.JSONDecodeError as exc:
            has_errors = True
            print(f"[INVALID JSON] {path}: {exc}")
            continue

        errors = validate_case(case)
        if errors:
            has_errors = True
            print(f"[INVALID] {path}")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"[OK] {path}")

    return 1 if has_errors else 0


def cmd_grade(args: argparse.Namespace) -> int:
    case_path = Path(args.case)
    original_path = Path(args.original)
    final_path = Path(args.final)

    try:
        case = load_json(case_path)
    except Exception as exc:  # noqa: BLE001
        report = build_report(
            {
                "id": case_path.stem,
                "skill": "unknown",
                "suite": "",
                "expected_state": {
                    "entities_expected_created": [],
                    "entities_expected_updated": [],
                    "entities_expected_unchanged": [],
                    "required_changes": [],
                    "forbidden_changes": [],
                    "tolerance_rules": [],
                },
            },
            {},
            {},
            bootstrap_error=f"case 读取失败: {exc}",
        )
        emit_report(report, args)
        return 1

    errors = validate_case(case)
    if errors:
        report = build_report(
            case,
            {},
            {},
            bootstrap_error="; ".join(errors),
        )
        emit_report(report, args)
        return 1

    try:
        original_state = load_json(original_path)
        final_state = load_json(final_path)
    except Exception as exc:  # noqa: BLE001
        report = build_report(
            case,
            {},
            {},
            bootstrap_error=f"状态快照读取失败: {exc}",
        )
        emit_report(report, args)
        return 1

    report = build_report(
        case,
        original_state,
        final_state,
        bootstrap_error=args.bootstrap_error,
        run_error=args.run_error,
    )
    emit_report(report, args)
    return 0 if report["status"] == "pass" else 1


def emit_report(report: dict[str, Any], args: argparse.Namespace) -> None:
    if args.output:
        dump_json(report, Path(args.output))

    if args.format == "markdown":
        print(render_markdown(report))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tri-state outcome-only eval harness")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate tri-state eval cases")
    validate_parser.add_argument("paths", nargs="+", help="Case file or directory")
    validate_parser.set_defaults(func=cmd_validate)

    grade_parser = subparsers.add_parser("grade", help="Grade a case with original/final snapshots")
    grade_parser.add_argument("--case", required=True, help="Case JSON path")
    grade_parser.add_argument("--original", required=True, help="original_state snapshot JSON")
    grade_parser.add_argument("--final", required=True, help="final_state snapshot JSON")
    grade_parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="json",
        help="Output report format",
    )
    grade_parser.add_argument("--output", help="Optional report output path")
    grade_parser.add_argument("--run-error", help="Mark the report as run_fail")
    grade_parser.add_argument("--bootstrap-error", help="Mark the report as bootstrap_fail")
    grade_parser.set_defaults(func=cmd_grade)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
