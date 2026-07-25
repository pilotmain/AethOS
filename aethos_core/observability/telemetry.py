# SPDX-License-Identifier: Apache-2.0
"""§8 Observability export — OpenTelemetry, structured logs, error sink, SLOs.

Everything here is optional and default-off so AethOS gains no new hard
dependency. OpenTelemetry and the Sentry-compatible error sink activate only
when their libraries are installed *and* the corresponding flag is set; otherwise
the helpers degrade to no-ops (or to the in-process metrics already collected by
``observability.metrics``).

Provides:
  * ``configure_telemetry()`` — startup wiring (JSON logs + OTel + error sink).
  * ``start_span(name)`` — context manager (OTel span if available, else noop).
  * ``record_chat_latency_ms`` / ``record_mutation_result`` — SLO signal feed.
  * ``capture_exception`` — route an error to the configured sink.
  * ``evaluate_slos()`` — compare live metrics to SLO targets → alert states.
"""

from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from typing import Any, Iterator

_log = logging.getLogger(__name__)

_OTEL_TRACER: Any = None
_SENTRY_READY = False
_CONFIGURED = False


# ─────────────────────────────── structured logs ──────────────────────────────


def _scrub(text: str) -> str:
    from aethos_core.config import get_settings
    from aethos_core.security.secret_redaction import redact_pii, redact_text

    out = redact_text(text)
    if getattr(get_settings(), "pii_redaction_enabled", True):
        out = redact_pii(out)
    return out


class _JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": record.created,
            "level": record.levelname,
            "logger": record.name,
            "msg": _scrub(record.getMessage()),
        }
        if record.exc_info:
            payload["exc"] = _scrub(self.formatException(record.exc_info))
        return json.dumps(payload, default=str)


def _configure_json_logging() -> None:
    root = logging.getLogger()
    for handler in root.handlers:
        handler.setFormatter(_JsonLogFormatter())
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(_JsonLogFormatter())
        root.addHandler(handler)


# ──────────────────────────────── OpenTelemetry ───────────────────────────────


def _configure_otel() -> None:
    global _OTEL_TRACER
    from aethos_core.config import get_settings

    s = get_settings()
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": s.otel_service_name})
        provider = TracerProvider(resource=resource)
        if s.otel_exporter_otlp_endpoint:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

            provider.add_span_processor(
                BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{s.otel_exporter_otlp_endpoint}/v1/traces"))
            )
        trace.set_tracer_provider(provider)
        _OTEL_TRACER = trace.get_tracer("aethos")
        _log.info("otel_configured service=%s endpoint=%s", s.otel_service_name, s.otel_exporter_otlp_endpoint or "(none)")
    except Exception:  # noqa: BLE001 — OTel libs absent or misconfigured → no-op
        _OTEL_TRACER = None
        _log.info("otel_unavailable (opentelemetry not installed); spans are no-ops")


@contextmanager
def start_span(name: str, **attrs: Any) -> Iterator[None]:
    if _OTEL_TRACER is None:
        yield
        return
    with _OTEL_TRACER.start_as_current_span(name) as span:  # pragma: no cover - needs otel
        for k, v in attrs.items():
            try:
                span.set_attribute(k, v)
            except Exception:  # noqa: BLE001
                pass
        yield


# ───────────────────────────────── error sink ─────────────────────────────────


def _configure_error_sink() -> None:
    global _SENTRY_READY
    from aethos_core.config import get_settings

    s = get_settings()
    if not (s.error_tracking_enabled and s.sentry_dsn):
        return
    try:
        import sentry_sdk

        sentry_sdk.init(dsn=s.sentry_dsn, traces_sample_rate=s.sentry_traces_sample_rate)
        _SENTRY_READY = True
        _log.info("error_sink_configured (sentry-compatible)")
    except Exception:  # noqa: BLE001
        _SENTRY_READY = False
        _log.info("error_sink_unavailable (sentry_sdk not installed)")


def capture_exception(exc: BaseException, **context: Any) -> None:
    if _SENTRY_READY:
        try:
            import sentry_sdk

            with sentry_sdk.push_scope() as scope:  # pragma: no cover - needs sentry
                for k, v in context.items():
                    scope.set_extra(k, v)
                sentry_sdk.capture_exception(exc)
            return
        except Exception:  # noqa: BLE001
            pass
    _log.error("captured_exception %s context=%s", exc, context, exc_info=exc)


# ──────────────────────────────── SLO signals ─────────────────────────────────


def record_chat_latency_ms(ms: float) -> None:
    from aethos_core.observability.metrics import observe

    observe("chat.latency_ms", float(ms))


def record_turn_timing(timing: dict[str, Any]) -> None:
    """Feed a turn's phase breakdown (router/model/tools/total ms) to metrics + OTEL.

    Best-effort and cheap: histograms power SLO/regression visibility, and a span
    carries the breakdown when OTel is enabled. Safe to call on every turn.
    """
    try:
        from aethos_core.observability.metrics import observe

        for key in ("total_ms", "router_ms", "model_ms", "tools_ms", "finalizer_ms"):
            val = timing.get(key)
            if val is None:
                continue
            observe(f"chat.turn.{key}", float(val))
    except Exception:  # noqa: BLE001
        pass
    if _OTEL_TRACER is not None:  # pragma: no cover - needs otel
        try:
            with start_span("chat.turn", **{k: float(v) for k, v in timing.items() if str(v).isdigit()}):
                pass
        except Exception:  # noqa: BLE001
            pass


def record_mutation_result(success: bool) -> None:
    from aethos_core.observability.metrics import increment

    increment("mutation.execute.total", 1.0)
    if success:
        increment("mutation.execute.success", 1.0)


def evaluate_slos() -> dict[str, Any]:
    """Compare live metrics to SLO targets and produce alert states."""
    from aethos_core.config import get_settings
    from aethos_core.observability.metrics import snapshot_metrics

    s = get_settings()
    snap = snapshot_metrics()
    counters = snap.get("counters") or {}
    hist = snap.get("histograms") or {}

    results: list[dict[str, Any]] = []

    chat_avg = float((hist.get("chat.latency_ms") or {}).get("avg") or 0.0)
    chat_samples = int((hist.get("chat.latency_ms") or {}).get("count") or 0)
    chat_ok = chat_samples == 0 or chat_avg <= s.slo_chat_latency_ms
    results.append(
        {
            "slo": "chat_latency_ms_avg",
            "target_max": s.slo_chat_latency_ms,
            "actual": round(chat_avg, 2),
            "samples": chat_samples,
            "ok": chat_ok,
            "severity": "ok" if chat_ok else "warning",
        }
    )

    total = float(counters.get("mutation.execute.total") or 0.0)
    success = float(counters.get("mutation.execute.success") or 0.0)
    rate = (success / total) if total else 1.0
    rate_ok = total == 0 or rate >= s.slo_mutation_success_rate
    results.append(
        {
            "slo": "mutation_success_rate",
            "target_min": s.slo_mutation_success_rate,
            "actual": round(rate, 4),
            "samples": int(total),
            "ok": rate_ok,
            "severity": "ok" if rate_ok else "critical",
        }
    )

    breached = [r for r in results if not r["ok"]]
    return {
        "ok": not breached,
        "slos": results,
        "alerts": breached,
        "collected_at": snap.get("collected_at"),
    }


# ───────────────────────────────── lifecycle ──────────────────────────────────


def configure_telemetry() -> dict[str, Any]:
    """Wire telemetry at startup. Idempotent; safe when optional libs absent."""
    global _CONFIGURED
    if _CONFIGURED:
        return telemetry_status()
    from aethos_core.config import get_settings

    s = get_settings()
    if s.log_format == "json":
        _configure_json_logging()
    if s.otel_enabled:
        _configure_otel()
    _configure_error_sink()
    _CONFIGURED = True
    return telemetry_status()


def telemetry_status() -> dict[str, Any]:
    from aethos_core.config import get_settings

    s = get_settings()
    return {
        "otel_enabled": bool(s.otel_enabled),
        "otel_active": _OTEL_TRACER is not None,
        "log_format": s.log_format,
        "error_tracking_enabled": bool(s.error_tracking_enabled),
        "error_sink_active": _SENTRY_READY,
        "configured": _CONFIGURED,
    }
