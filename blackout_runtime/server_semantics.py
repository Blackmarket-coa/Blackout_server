from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

BLACKOUT_CHANNEL_TYPE_EVENT = "m.blackout.channel.type"
GOVERNANCE_PROPOSAL_EVENT = "m.blackout.governance.proposal"
GOVERNANCE_VOTE_EVENT = "m.blackout.governance.vote"
REPUTATION_UPDATE_EVENT = "m.blackout.reputation.update"

BLACKOUT_PRESENCE_ROUTE = "/_synapse/client/blackout/presence"

_ALLOWED_PRESENCE = {
    "delivering",
    "available_for_claims",
    "off_duty",
    "in_governance_session",
}

PRESET_TO_CHANNEL_TYPE = {
    "blackout_cell_space": "blackout_cell_space",
    "blackout_dead_drop_room": "blackout_dead_drop_room",
    "blackout_announcement_room": "blackout_announcement_room",
}


@dataclass(frozen=True)
class RoomTemplate:
    join_rule: str
    power_levels: Mapping[str, object]
    allowed_event_types: Sequence[str]
    extra_state_events: Mapping[str, Mapping[str, object]] = field(default_factory=dict)


ROOM_TEMPLATES: Dict[str, RoomTemplate] = {
    "voice": RoomTemplate(
        join_rule="invite",
        power_levels={"events_default": 50, "state_default": 100},
        allowed_event_types=("m.room.message", "m.call.invite", BLACKOUT_CHANNEL_TYPE_EVENT),
    ),
    "forum": RoomTemplate(
        join_rule="public",
        power_levels={"events_default": 0, "state_default": 50},
        allowed_event_types=("m.room.message", "m.room.topic", BLACKOUT_CHANNEL_TYPE_EVENT),
    ),
    "governance": RoomTemplate(
        join_rule="invite",
        power_levels={"events_default": 0, "state_default": 100},
        allowed_event_types=(
            "m.room.message",
            GOVERNANCE_PROPOSAL_EVENT,
            GOVERNANCE_VOTE_EVENT,
            REPUTATION_UPDATE_EVENT,
            BLACKOUT_CHANNEL_TYPE_EVENT,
        ),
    ),
    "dispute": RoomTemplate(
        join_rule="invite",
        power_levels={"events_default": 0, "state_default": 100},
        allowed_event_types=(
            "m.room.message",
            GOVERNANCE_PROPOSAL_EVENT,
            GOVERNANCE_VOTE_EVENT,
            BLACKOUT_CHANNEL_TYPE_EVENT,
        ),
    ),
    "blackout_cell_space": RoomTemplate(
        join_rule="invite",
        power_levels={"events_default": 0, "state_default": 100},
        allowed_event_types=(
            "m.room.topic",
            "m.space.child",
            "m.space.parent",
            BLACKOUT_CHANNEL_TYPE_EVENT,
        ),
        extra_state_events={
            "m.room.guest_access": {"guest_access": "forbidden"},
            "m.room.history_visibility": {"history_visibility": "joined"},
        },
    ),
    "blackout_dead_drop_room": RoomTemplate(
        join_rule="invite",
        power_levels={"events_default": 0, "state_default": 100},
        allowed_event_types=(
            "m.room.message",
            BLACKOUT_CHANNEL_TYPE_EVENT,
        ),
        extra_state_events={
            "m.room.history_visibility": {"history_visibility": "joined"},
            "m.room.guest_access": {"guest_access": "forbidden"},
            "m.room.retention": {"max_lifetime": 86_400_000},
        },
    ),
    "blackout_announcement_room": RoomTemplate(
        join_rule="invite",
        power_levels={
            "events_default": 50,
            "state_default": 100,
            "events": {"m.room.message": 50},
        },
        allowed_event_types=(
            "m.room.message",
            "m.room.topic",
            BLACKOUT_CHANNEL_TYPE_EVENT,
        ),
        extra_state_events={
            "m.room.history_visibility": {"history_visibility": "joined"},
            "m.room.guest_access": {"guest_access": "forbidden"},
        },
    ),
}


class BlackoutServerSemantics:
    """Pure-python helper for module callback logic and schema validation."""

    def on_create_room(self, config: MutableMapping[str, object]) -> None:
        creation_content = config.get("creation_content", {})
        if not isinstance(creation_content, Mapping):
            raise ValueError("creation_content must be an object")

        channel_type = creation_content.get("m.blackout.channel.type")
        if channel_type is None:
            preset = config.get("preset")
            if isinstance(preset, str):
                channel_type = PRESET_TO_CHANNEL_TYPE.get(preset)
            if channel_type is None:
                return

        template = ROOM_TEMPLATES.get(str(channel_type))
        if template is None:
            raise ValueError(f"Unsupported blackout channel type: {channel_type}")

        if "creation_content" not in config or not isinstance(config["creation_content"], MutableMapping):
            config["creation_content"] = dict(creation_content)
        config["creation_content"]["m.blackout.channel.type"] = channel_type

        initial_state = config.setdefault("initial_state", [])
        if not isinstance(initial_state, list):
            raise ValueError("initial_state must be a list")

        self._upsert_initial_state(
            initial_state,
            event_type="m.room.join_rules",
            content={"join_rule": template.join_rule},
        )
        self._upsert_initial_state(
            initial_state,
            event_type="m.room.power_levels",
            content=dict(template.power_levels),
            merge_content=True,
        )
        self._upsert_initial_state(
            initial_state,
            event_type=BLACKOUT_CHANNEL_TYPE_EVENT,
            content={"channel_type": channel_type},
        )

        for event_type, content in template.extra_state_events.items():
            self._upsert_initial_state(
                initial_state,
                event_type=event_type,
                content=content,
            )

    def check_event_allowed(
        self,
        event_type: str,
        content: Mapping[str, object],
        *,
        channel_type: str | None = None,
    ) -> bool:
        if event_type == BLACKOUT_CHANNEL_TYPE_EVENT:
            self._validate_channel_type(content)
            return True

        if event_type == GOVERNANCE_PROPOSAL_EVENT:
            self._validate_governance_proposal(content)
            return True

        if event_type == GOVERNANCE_VOTE_EVENT:
            self._validate_governance_vote(content)
            return True

        if event_type == REPUTATION_UPDATE_EVENT:
            self._validate_reputation_update(content)
            return True

        if channel_type and channel_type in ROOM_TEMPLATES:
            if event_type not in ROOM_TEMPLATES[channel_type].allowed_event_types:
                raise ValueError(
                    f"Event type {event_type} is not allowed in {channel_type} rooms"
                )

        return True

    @staticmethod
    def _upsert_initial_state(
        initial_state: List[MutableMapping[str, object]],
        *,
        event_type: str,
        content: Mapping[str, object],
        merge_content: bool = False,
    ) -> None:
        for event in initial_state:
            if event.get("type") == event_type and event.get("state_key", "") == "":
                if merge_content and isinstance(event.get("content"), Mapping):
                    merged = dict(event["content"])
                    merged.update(content)
                    event["content"] = merged
                else:
                    event["content"] = dict(content)
                return

        initial_state.append(
            {"type": event_type, "state_key": "", "content": dict(content)}
        )

    @staticmethod
    def _validate_channel_type(content: Mapping[str, object]) -> None:
        channel_type = content.get("channel_type")
        if channel_type not in ROOM_TEMPLATES:
            raise ValueError("m.blackout.channel.type requires a supported channel_type")

    @staticmethod
    def _validate_governance_proposal(content: Mapping[str, object]) -> None:
        required = ("proposal_id", "title", "options", "opens_at", "closes_at")
        missing = [key for key in required if key not in content]
        if missing:
            raise ValueError(f"governance proposal missing required fields: {missing}")

        options = content["options"]
        if not isinstance(options, list) or len(options) < 2:
            raise ValueError("governance proposal options must contain at least two entries")
        if not all(isinstance(option, str) and option for option in options):
            raise ValueError("governance proposal options must be non-empty strings")

    @staticmethod
    def _validate_governance_vote(content: Mapping[str, object]) -> None:
        required = ("proposal_id", "vote")
        missing = [key for key in required if key not in content]
        if missing:
            raise ValueError(f"governance vote missing required fields: {missing}")

        if not isinstance(content["vote"], str) or not content["vote"]:
            raise ValueError("governance vote requires non-empty string vote")

    @staticmethod
    def _validate_reputation_update(content: Mapping[str, object]) -> None:
        required = ("node_id", "delta", "reason")
        missing = [key for key in required if key not in content]
        if missing:
            raise ValueError(f"reputation update missing required fields: {missing}")

        if not isinstance(content["delta"], (int, float)):
            raise ValueError("reputation update delta must be numeric")


class BlackoutPresenceService:
    def __init__(self) -> None:
        self._presence: Dict[str, str] = {}

    def set_presence(self, user_id: str, state: str) -> None:
        if state not in _ALLOWED_PRESENCE:
            raise ValueError(f"Unsupported blackout presence state: {state}")
        self._presence[user_id] = state

    def get_presence(self, user_id: str) -> str | None:
        return self._presence.get(user_id)

    def bulk_get(self, user_ids: Iterable[str]) -> Dict[str, str]:
        return {user_id: state for user_id in user_ids if (state := self._presence.get(user_id))}
