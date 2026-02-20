from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from typing import Iterable, List, Optional

from .crdt import AutomergePrototypeCRDT, CRDTOperation
from .envelope import EventEnvelope


@dataclass
class LowMemoryProfile:
    max_pending_events: int = 2048
    max_snapshot_bytes: int = 4 * 1024 * 1024
    replay_batch_size: int = 256


class BlackoutNodeRuntime:
    """Snapshot + replay boot and offline rejoin recovery runtime path."""

    def __init__(self, profile: Optional[LowMemoryProfile] = None) -> None:
        self.profile = profile or LowMemoryProfile()
        self.crdt = AutomergePrototypeCRDT()
        self._event_log: List[EventEnvelope] = []

    def boot_from_snapshot_and_replay(
        self, *, snapshot: dict, replay_events: Iterable[EventEnvelope]
    ) -> None:
        self.crdt.import_snapshot(snapshot)
        self._event_log = []

        expected_previous_hash = "genesis"
        for event in replay_events:
            if not event.verify_signature():
                raise ValueError(f"Invalid event signature for {event.event_id}")
            if not event.verify_previous_hash(expected_previous_hash):
                raise ValueError(
                    f"Broken hash chain for {event.event_id}: expected {expected_previous_hash}, got {event.previous_hash}"
                )
            self._apply_event(event)
            expected_previous_hash = event.digest()

    def recover_offline_rejoin(
        self, *, last_known_hash: str, peer_events: Iterable[EventEnvelope]
    ) -> int:
        buffered = list(peer_events)
        if len(buffered) > self.profile.max_pending_events:
            raise ValueError("Peer replay set exceeds low-memory pending-event budget")

        start_index = 0
        if last_known_hash != "genesis":
            for index, event in enumerate(buffered):
                if event.previous_hash == last_known_hash:
                    start_index = index
                    break
            else:
                raise ValueError("Unable to locate replay starting point from peer events")

        expected_previous_hash = last_known_hash
        applied = 0
        for event in buffered[start_index:]:
            if not event.verify_signature() or not event.verify_previous_hash(
                expected_previous_hash
            ):
                continue
            self._apply_event(event)
            expected_previous_hash = event.digest()
            applied += 1
        return applied

    def export_snapshot(self) -> dict:
        snapshot = self.crdt.snapshot()
        encoded = json.dumps(snapshot).encode("utf-8")
        if len(encoded) > self.profile.max_snapshot_bytes:
            raise ValueError("Snapshot exceeds low-memory profile target")
        return snapshot

    def last_hash(self) -> str:
        if not self._event_log:
            return "genesis"
        return self._event_log[-1].digest()

    def _apply_event(self, event: EventEnvelope) -> None:
        payload = json.loads(base64.b64decode(event.encrypted_payload).decode("utf-8"))
        self.crdt.apply(
            CRDTOperation(
                key=str(payload["key"]),
                value=str(payload["value"]),
                site=event.crdt_site,
                counter=event.crdt_counter,
            )
        )
        self._event_log.append(event)
