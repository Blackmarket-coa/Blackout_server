import pytest

from blackout_runtime.server_semantics import (
    BLACKOUT_CHANNEL_TYPE_EVENT,
    BLACKOUT_PRESENCE_ROUTE,
    ANNOUNCEMENT_POLICY_EVENT,
    GOVERNANCE_PROPOSAL_EVENT,
    GOVERNANCE_VOTE_EVENT,
    REPUTATION_UPDATE_EVENT,
    BlackoutPresenceService,
    BlackoutServerSemantics,
)


@pytest.mark.parametrize("channel_type", ["voice", "forum", "governance", "dispute", "blackout_cell_space", "blackout_dead_drop_room", "blackout_announcement_room"])
def test_on_create_room_enforces_template(channel_type: str) -> None:
    semantics = BlackoutServerSemantics()
    config = {"creation_content": {"m.blackout.channel.type": channel_type}}

    semantics.on_create_room(config)

    initial_state = config["initial_state"]
    types = {event["type"] for event in initial_state}
    assert "m.room.join_rules" in types
    assert "m.room.power_levels" in types
    assert BLACKOUT_CHANNEL_TYPE_EVENT in types


def test_on_create_room_rejects_unknown_channel_type() -> None:
    semantics = BlackoutServerSemantics()
    with pytest.raises(ValueError, match="Unsupported blackout channel type"):
        semantics.on_create_room(
            {"creation_content": {"m.blackout.channel.type": "unknown"}}
        )


def test_validate_custom_event_schemas_accepts_valid_payloads() -> None:
    semantics = BlackoutServerSemantics()

    assert semantics.check_event_allowed(
        GOVERNANCE_PROPOSAL_EVENT,
        {
            "proposal_id": "p1",
            "title": "Activate depot",
            "options": ["yes", "no"],
            "opens_at": 1,
            "closes_at": 2,
        },
    )
    assert semantics.check_event_allowed(
        GOVERNANCE_VOTE_EVENT,
        {"proposal_id": "p1", "vote": "yes"},
    )
    assert semantics.check_event_allowed(
        REPUTATION_UPDATE_EVENT,
        {"node_id": "node-7", "delta": 2, "reason": "delivery_success"},
    )
    assert semantics.check_event_allowed(
        BLACKOUT_CHANNEL_TYPE_EVENT,
        {"channel_type": "governance"},
    )


@pytest.mark.parametrize(
    ("event_type", "content", "error"),
    [
        (
            GOVERNANCE_PROPOSAL_EVENT,
            {"proposal_id": "p1", "title": "bad", "options": ["yes"]},
            "missing required fields",
        ),
        (
            GOVERNANCE_VOTE_EVENT,
            {"proposal_id": "p1", "vote": ""},
            "non-empty string vote",
        ),
        (
            REPUTATION_UPDATE_EVENT,
            {"node_id": "n1", "delta": "x", "reason": "bad"},
            "delta must be numeric",
        ),
        (
            BLACKOUT_CHANNEL_TYPE_EVENT,
            {"channel_type": "invalid"},
            "supported channel_type",
        ),
    ],
)
def test_validate_custom_event_schemas_rejects_malformed_payloads(
    event_type: str, content: dict, error: str
) -> None:
    semantics = BlackoutServerSemantics()
    with pytest.raises(ValueError, match=error):
        semantics.check_event_allowed(event_type, content)


def test_channel_template_blocks_unapproved_event_types() -> None:
    semantics = BlackoutServerSemantics()

    with pytest.raises(ValueError, match="not allowed"):
        semantics.check_event_allowed(
            "m.room.server_acl", {"allow": []}, channel_type="voice"
        )


def test_extended_presence_endpoint_and_states() -> None:
    presence = BlackoutPresenceService()
    presence.set_presence("@alice:test", "delivering")

    assert BLACKOUT_PRESENCE_ROUTE == "/_synapse/client/blackout/presence"
    assert presence.get_presence("@alice:test") == "delivering"

    with pytest.raises(ValueError, match="Unsupported blackout presence state"):
        presence.set_presence("@alice:test", "online")


def test_on_create_room_preset_wiring_for_cell_and_dead_drop() -> None:
    semantics = BlackoutServerSemantics()

    cell_config = {"preset": "blackout_cell_space"}
    semantics.on_create_room(cell_config)
    cell_state = {event["type"]: event["content"] for event in cell_config["initial_state"]}
    assert cell_config["creation_content"]["m.blackout.channel.type"] == "blackout_cell_space"
    assert cell_state["m.room.join_rules"]["join_rule"] == "invite"
    assert cell_state["m.room.guest_access"]["guest_access"] == "forbidden"

    dead_drop_config = {"preset": "blackout_dead_drop_room"}
    semantics.on_create_room(dead_drop_config)
    dead_drop_state = {event["type"]: event["content"] for event in dead_drop_config["initial_state"]}
    assert dead_drop_config["creation_content"]["m.blackout.channel.type"] == "blackout_dead_drop_room"
    assert dead_drop_state["m.room.join_rules"]["join_rule"] == "invite"
    assert dead_drop_state["m.room.history_visibility"]["history_visibility"] == "joined"


def test_dead_drop_template_blocks_unapproved_event_types() -> None:
    semantics = BlackoutServerSemantics()

    with pytest.raises(ValueError, match="not allowed"):
        semantics.check_event_allowed(
            "m.room.topic", {"topic": "not allowed"}, channel_type="blackout_dead_drop_room"
        )


def test_announcement_preset_history_visibility_and_event_allowlist() -> None:
    semantics = BlackoutServerSemantics()
    config = {"preset": "blackout_announcement_room"}
    semantics.on_create_room(config)

    by_type = {entry["type"]: entry["content"] for entry in config["initial_state"]}
    assert by_type["m.room.history_visibility"]["history_visibility"] == "joined"

    with pytest.raises(ValueError, match="not allowed"):
        semantics.check_event_allowed(
            "m.room.encrypted", {"ciphertext": "x"}, channel_type="blackout_announcement_room"
        )


def test_cell_space_applies_federation_acl_template_by_trust_tier() -> None:
    semantics = BlackoutServerSemantics()

    config = {
        "preset": "blackout_cell_space",
        "creation_content": {"blackout.federation.trust_tier": "restricted"},
    }
    semantics.on_create_room(config)

    by_type = {entry["type"]: entry["content"] for entry in config["initial_state"]}
    assert by_type["m.room.server_acl"]["deny"] == ["*"]
    assert by_type["m.room.server_acl"]["allow"] == ["*.local"]


def test_cell_space_rejects_unknown_trust_tier() -> None:
    semantics = BlackoutServerSemantics()
    with pytest.raises(ValueError, match="Unsupported federation trust tier"):
        semantics.on_create_room(
            {
                "preset": "blackout_cell_space",
                "creation_content": {"blackout.federation.trust_tier": "internet"},
            }
        )


def test_validate_announcement_policy_event() -> None:
    semantics = BlackoutServerSemantics()
    assert semantics.check_event_allowed(
        ANNOUNCEMENT_POLICY_EVENT,
        {
            "sender_roles": ["announcer", "moderator"],
            "fanout_mode": "delayed_window",
            "delayed_fanout_min_ms": 5000,
            "delayed_fanout_max_ms": 15000,
            "rollback_procedure_ref": "docs/ops/announcement_fanout_rollback.md",
        },
    )

    with pytest.raises(ValueError, match="requires rollback_procedure_ref"):
        semantics.check_event_allowed(
            ANNOUNCEMENT_POLICY_EVENT,
            {
                "sender_roles": ["announcer"],
                "fanout_mode": "delayed_window",
                "delayed_fanout_min_ms": 5000,
                "delayed_fanout_max_ms": 15000,
            },
        )
