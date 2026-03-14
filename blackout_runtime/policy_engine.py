from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Mapping, MutableMapping, Optional, Sequence


DEFAULT_FEATURE_FLAGS: Dict[str, bool] = {
    "cell_governance_templates": False,
    "dead_drop_room_preset": False,
    "announcement_room_preset": False,
    "timing_jitter_worker": False,
    "delayed_broadcast_fanout": False,
    "edge_federation_profile": False,
}

FEDERATION_TRUST_TIER_ACLS: Dict[str, Dict[str, Sequence[str]]] = {
    "local": {"allow": ["*.local"], "deny": []},
    "partner": {"allow": ["*.local", "partner.example"], "deny": []},
    "restricted": {"allow": ["*.local"], "deny": ["*"]},
}


@dataclass(frozen=True)
class RollbackCriteria:
    metric: str
    threshold: float
    comparator: str
    runbook_ref: str


@dataclass(frozen=True)
class PilotDecision:
    should_rollback: bool
    reason: str


class BlackoutPolicyEngine:
    def __init__(self, feature_flags: Optional[Mapping[str, bool]] = None) -> None:
        self._feature_flags = dict(DEFAULT_FEATURE_FLAGS)
        if feature_flags:
            self._feature_flags.update(feature_flags)

    def feature_enabled(self, name: str) -> bool:
        return bool(self._feature_flags.get(name, False))

    def build_room_preset(
        self,
        preset_name: str,
        *,
        ttl_hours: Optional[int] = None,
        fanout_mode: str = "immediate",
    ) -> MutableMapping[str, object]:
        if preset_name == "blackout_cell_space":
            self._require("cell_governance_templates")
            return {
                "name": preset_name,
                "visibility": "private",
                "join_rule": "invite",
                "history_visibility": "joined",
                "federation_trust_tier": "local",
            }

        if preset_name == "blackout_dead_drop_room":
            self._require("dead_drop_room_preset")
            value = ttl_hours if ttl_hours is not None else 24
            if value < 1 or value > 168:
                raise ValueError("retention_ttl_hours must be between 1 and 168")
            return {
                "name": preset_name,
                "visibility": "private",
                "join_rule": "invite",
                "history_visibility": "joined",
                "retention_ttl_hours": value,
                "purge_mode": "hard_delete",
                "max_members": 12,
            }

        if preset_name == "blackout_announcement_room":
            self._require("announcement_room_preset")
            if fanout_mode == "delayed_window" and not self.feature_enabled(
                "delayed_broadcast_fanout"
            ):
                raise ValueError("delayed fanout requires delayed_broadcast_fanout feature")
            return {
                "name": preset_name,
                "visibility": "private",
                "sender_roles": ["announcer", "moderator"],
                "default_member_power": 0,
                "read_receipt_policy": "minimized",
                "fanout_mode": fanout_mode,
            }

        raise ValueError(f"Unsupported preset: {preset_name}")

    def enforce_membership_boundary(self, *, chapter_id: str, member_chapter_id: str) -> bool:
        return chapter_id == member_chapter_id

    def can_sender_broadcast(self, sender_role: str) -> bool:
        return sender_role in {"announcer", "moderator"}

    def trust_tier_acl(self, tier: str) -> Dict[str, Sequence[str]]:
        if tier not in FEDERATION_TRUST_TIER_ACLS:
            raise ValueError(f"Unsupported trust tier: {tier}")
        return dict(FEDERATION_TRUST_TIER_ACLS[tier])

    def compute_jitter_delay_ms(self, *, min_seconds: int, max_seconds: int) -> int:
        self._require("timing_jitter_worker")
        if min_seconds < 0 or max_seconds < min_seconds:
            raise ValueError("invalid jitter delay bounds")
        return random.randint(min_seconds, max_seconds) * 1000

    def choose_broadcast_delay_ms(self, *, min_seconds: int, max_seconds: int) -> int:
        self._require("delayed_broadcast_fanout")
        if min_seconds < 1 or max_seconds < min_seconds:
            raise ValueError("invalid delayed fanout bounds")
        return random.randint(min_seconds, max_seconds) * 1000

    def evaluate_pilot_guardrail(
        self,
        *,
        observed_value: float,
        criteria: RollbackCriteria,
    ) -> PilotDecision:
        if criteria.comparator == ">":
            breached = observed_value > criteria.threshold
        elif criteria.comparator == "<":
            breached = observed_value < criteria.threshold
        else:
            raise ValueError("Unsupported comparator")

        if breached:
            return PilotDecision(
                should_rollback=True,
                reason=(
                    f"{criteria.metric} breached {criteria.comparator} {criteria.threshold}; "
                    f"execute rollback via {criteria.runbook_ref}"
                ),
            )

        return PilotDecision(should_rollback=False, reason="within SLO guardrail")

    def _require(self, feature_flag: str) -> None:
        if not self.feature_enabled(feature_flag):
            raise ValueError(f"Feature flag '{feature_flag}' is disabled")
