"""
3.1. Инструменты для телеметрии. 
"""

from dataclasses import dataclass, asdict, field
import time
from typing import Any, Optional, TypeVar

from langchain_protocol import RunResult
from pydantic_ai import Agent
from config import Config
import json

from pydantic import BaseModel

# Приблизительный прайс-лист OpenRouter (USD за 1M токенов, вход/выход).
PRICING: dict[str, dict[str, float]] = {
    "openai:gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "openai:gpt-4o": {"input": 2.50, "output": 10.00},
    "openai:gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    "openai:gpt-4.1": {"input": 2.00, "output": 8.00},
    "anthropic:claude-3.5-haiku": {"input": 1.00, "output": 5.00},
    "meta-llama/llama-3.1-8b-instruct": {"input": 0.05, "output": 0.08},
}
DEFAULT_PRICE = {"input": 0.15, "output": 0.60}


def _pricing_for(model_name: str) -> dict[str, float]:
    return PRICING.get(model_name, DEFAULT_PRICE)


def estimate_tokens_from_text(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


@dataclass
class TraceRecord:
    scenario_id: str
    scenario_label: str
    framework: str
    step: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    usd_cost: float
    model: str
    token_source: str = "usage"
    extra: dict = field(default_factory=dict)


TRACES: list[TraceRecord] = []


def reset_traces() -> None:
    TRACES.clear()


def _extract_usage(result) -> tuple[int, int, str]:
    usage_obj = None
    for attr in ("usage", "get_usage"):
        candidate = getattr(result, attr, None)
        if callable(candidate):
            try:
                usage_obj = candidate()
            except TypeError:
                usage_obj = None
            break
        if candidate is not None:
            usage_obj = candidate
            break

    """
    Эта функция — «универсальный преобразователь» в целое число. Она нужна, чтобы гарантированно получить 
    int (число токенов), даже если данные пришли в «кривом» или неожиданном формате.
    """
    def _coerce(obj, name: str) -> int | None:
        if obj is None:
            return None
        value = obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    request_tokens = _coerce(usage_obj, "request_tokens") or _coerce(usage_obj, "input_tokens")
    response_tokens = _coerce(usage_obj, "response_tokens") or _coerce(usage_obj, "output_tokens")
    if request_tokens is not None or response_tokens is not None:
        return (request_tokens or 0, response_tokens or 0, "usage")

    text = ""
    output = getattr(result, "output", None)
    if hasattr(output, "model_dump_json"):
        try:
            if isinstance(output, BaseModel):
              text = output.model_dump_json()
            else:
              text = ""
        except Exception:
            text = ""
    elif isinstance(output, str):
        text = output
    return (0, estimate_tokens_from_text(text), "estimate")


def _compute_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    price = _pricing_for(model_name)
    return round(
        input_tokens / 1_000_000 * price["input"]
        + output_tokens / 1_000_000 * price["output"],
        6,
    )

TDeps = TypeVar("TDeps")

async def run_with_telemetry(
    agent: Agent[Any, TDeps],
    prompt,
    *,
    scenario_id: str,
    scenario_label: str,
    framework: str,
    step: str,
    model: str | None = None,
    extra: dict | None = None,
    deps: Optional[TDeps] = None,
):
    '''Оборачивает agent.run(...) и складывает latency/tokens/cost в TRACES.'''
    model_name = model or Config.DEFAULT_MODEL
    t0 = time.perf_counter()
    result = await agent.run(prompt, deps=deps)
    latency_ms = (time.perf_counter() - t0) * 1000
    input_tokens, output_tokens, source = _extract_usage(result)
    usd_cost = _compute_cost(model_name, input_tokens, output_tokens)
    TRACES.append(
        TraceRecord(
            scenario_id=scenario_id,
            scenario_label=scenario_label,
            framework=framework,
            step=step,
            latency_ms=round(latency_ms, 1),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            usd_cost=usd_cost,
            model=model_name,
            token_source=source,
            extra=extra or {},
        )
    )
    return result


def print_telemetry_table(records: list[TraceRecord] | None = None) -> None:
    records = records if records is not None else TRACES
    if not records:
        print("Нет записей телеметрии — запусти агентов выше.")
        return
    headers = ["scenario", "framework", "step", "latency_ms", "in_tok", "out_tok", "usd_cost", "src"]
    rows = [
        [
            r.scenario_id,
            r.framework,
            r.step,
            f"{r.latency_ms:.0f}",
            str(r.input_tokens),
            str(r.output_tokens),
            f"{r.usd_cost:.6f}",
            r.token_source,
        ]
        for r in records
    ]
    widths = [max(len(h), *(len(row[i]) for row in rows)) for i, h in enumerate(headers)]

    def _fmt(values: list[str]) -> str:
        return "  ".join(v.ljust(widths[i]) for i, v in enumerate(values))

    line = "-" * (sum(widths) + 2 * (len(widths) - 1))
    print(_fmt(headers))
    print(line)
    for row in rows:
        print(_fmt(row))

    total_cost = sum(r.usd_cost for r in records)
    total_latency = sum(r.latency_ms for r in records)
    print(line)
    print(f"Итого: latency_ms={total_latency:.0f} ; usd_cost~={total_cost:.4f}")


def aggregate_by_scenario_and_framework(records: list[TraceRecord] | None = None) -> dict:
    records = records if records is not None else TRACES
    result: dict[tuple[str, str], dict] = {}
    for r in records:
        key = (r.scenario_id, r.framework)
        bucket = result.setdefault(
            key,
            {
                "scenario_id": r.scenario_id,
                "scenario_label": r.scenario_label,
                "framework": r.framework,
                "latency_ms": 0.0,
                "input_tokens": 0,
                "output_tokens": 0,
                "usd_cost": 0.0,
                "steps": 0,
            },
        )
        bucket["latency_ms"] += r.latency_ms
        bucket["input_tokens"] += r.input_tokens
        bucket["output_tokens"] += r.output_tokens
        bucket["usd_cost"] += r.usd_cost
        bucket["steps"] += 1
    for bucket in result.values():
        bucket["latency_ms"] = round(bucket["latency_ms"], 1)
        bucket["usd_cost"] = round(bucket["usd_cost"], 6)
    return result


def export_metrics_json(path: str = "examples/metrics.json") -> dict:
    '''Сбрасывает метрики в JSON; этот же файл читает генератор PPTX.'''
    from pathlib import Path

    aggregated = aggregate_by_scenario_and_framework()
    payload = {
        "model": Config.DEFAULT_MODEL,
        "records": [asdict(r) for r in TRACES],
        "aggregated": list(aggregated.values()),
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Метрики выгружены в {target.resolve()} ({len(TRACES)} traces)")
    return payload