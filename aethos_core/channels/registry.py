# SPDX-License-Identifier: Apache-2.0
"""Channel registry — transports only, not orchestration brains."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.channels.base.channel_adapter import ChannelAdapter


@dataclass
class ChannelCapability:
    inbound: bool = False
    outbound: bool = False
    approval_transport: bool = False
    evidence_transport: bool = False


@dataclass
class ChannelSpec:
    name: str
    label: str
    # active = configured + operational; ready = transport implemented (add credentials);
    # stub = adapter incomplete; planned = not built yet
    status: str  # active | ready | stub | planned
    capabilities: ChannelCapability = field(default_factory=ChannelCapability)
    adapter: ChannelAdapter | None = None


# Transports with adapters, webhook routes, and governed inbound→reply→outbound paths.
_TRANSPORT_READY_CHANNELS = frozenset({"slack", "discord", "email", "whatsapp", "messenger"})


_CHANNEL_SPECS: dict[str, ChannelSpec] = {
    "web": ChannelSpec(
        name="web",
        label="Web / Mission Control",
        status="active",
        capabilities=ChannelCapability(
            inbound=True, outbound=True, approval_transport=True, evidence_transport=True
        ),
    ),
    "telegram": ChannelSpec(
        name="telegram",
        label="Telegram",
        status="active",
        capabilities=ChannelCapability(
            inbound=True, outbound=True, approval_transport=True, evidence_transport=True
        ),
    ),
    "email": ChannelSpec(name="email", label="Email", status="ready"),
    "slack": ChannelSpec(name="slack", label="Slack", status="ready"),
    "teams": ChannelSpec(name="teams", label="Microsoft Teams", status="stub"),
    "discord": ChannelSpec(name="discord", label="Discord", status="ready"),
    "whatsapp": ChannelSpec(name="whatsapp", label="WhatsApp", status="ready"),
    "messenger": ChannelSpec(name="messenger", label="Messenger", status="ready"),
    "sms": ChannelSpec(name="sms", label="SMS", status="stub"),
    "voice": ChannelSpec(name="voice", label="Voice", status="stub"),
    "social_dm": ChannelSpec(name="social_dm", label="Social DMs", status="planned"),
    "webhook": ChannelSpec(name="webhook", label="Webhook / API channel", status="planned"),
    "desktop": ChannelSpec(name="desktop", label="Desktop shell", status="planned"),
    "mobile": ChannelSpec(name="mobile", label="Mobile shell", status="planned"),
}


def list_channels(*, include_planned: bool = True) -> list[ChannelSpec]:
    specs = list(_CHANNEL_SPECS.values())
    if include_planned:
        return specs
    return [s for s in specs if s.status == "active"]


def get_channel(name: str) -> ChannelSpec | None:
    return _CHANNEL_SPECS.get(name.strip().lower())


def format_channel_summary() -> str:
    lines = ["**Supported channels**", ""]
    for spec in list_channels():
        cap = spec.capabilities
        extras = []
        if cap.approval_transport:
            extras.append("approvals")
        if cap.evidence_transport:
            extras.append("evidence")
        extra = f" ({', '.join(extras)})" if extras else ""
        lines.append(f"- **{spec.label}** — `{spec.status}`{extra}")
    lines.extend(
        [
            "",
            "Channels are transports only. Orchestration lifecycle, policy, and adapters live in the core brain.",
        ]
    )
    return "\n".join(lines)


def channel_registry_dict() -> dict[str, Any]:
    return {
        "channels": [
            {
                "name": s.name,
                "label": s.label,
                "status": s.status,
                "capabilities": {
                    "inbound": s.capabilities.inbound,
                    "outbound": s.capabilities.outbound,
                    "approval_transport": s.capabilities.approval_transport,
                    "evidence_transport": s.capabilities.evidence_transport,
                },
            }
            for s in list_channels()
        ]
    }
