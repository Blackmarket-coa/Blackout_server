import base64
import json

from nacl.signing import SigningKey

from blackout_runtime.envelope import EventEnvelope
from blackout_runtime.runtime import BlackoutNodeRuntime


def _event(
    signing_key: SigningKey, previous_hash: str, key: str, value: str, counter: int
) -> EventEnvelope:
    payload = base64.b64encode(
        json.dumps({"key": key, "value": value}).encode("utf-8")
    ).decode("ascii")
    return EventEnvelope.create(
        signing_key=signing_key,
        event_type="MESSAGE_CREATED",
        encrypted_payload=payload,
        previous_hash=previous_hash,
        room_id="!room:test",
        crdt_site="peer-a",
        crdt_counter=counter,
    )


def test_boot_from_snapshot_and_replay() -> None:
    key = SigningKey.generate()
    first = _event(key, "genesis", "topic", "hello", 1)
    second = _event(key, first.digest(), "topic", "world", 2)

    runtime = BlackoutNodeRuntime()
    runtime.boot_from_snapshot_and_replay(snapshot={}, replay_events=[first, second])

    assert runtime.crdt.values()["topic"] == "world"
    assert runtime.last_hash() == second.digest()


def test_recover_offline_rejoin_applies_missing_range() -> None:
    key = SigningKey.generate()
    first = _event(key, "genesis", "a", "1", 1)
    second = _event(key, first.digest(), "b", "2", 2)

    runtime = BlackoutNodeRuntime()
    runtime.boot_from_snapshot_and_replay(snapshot={}, replay_events=[first])

    applied = runtime.recover_offline_rejoin(
        last_known_hash=first.digest(),
        peer_events=[second],
    )

    assert applied == 1
    assert runtime.crdt.values()["b"] == "2"
