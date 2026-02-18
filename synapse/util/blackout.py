import base64
import re
from dataclasses import dataclass
from typing import Any, Dict, List


_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")


@dataclass(frozen=True)
class BlackoutSignalValidationResult:
    missing_redundancy_metadata: bool = False
    invalid_redundancy_metadata: bool = False


def _is_fixed_length_hash(value: Any) -> bool:
    if not isinstance(value, str):
        return False

    # Accept SHA-256 hashes encoded as hex.
    if len(value) == 64 and _HEX_RE.fullmatch(value):
        return True

    # Accept SHA-256 hashes encoded as base64.
    padded = value + ("=" * ((4 - (len(value) % 4)) % 4))
    try:
        decoded = base64.b64decode(padded, validate=True)
    except Exception:
        return False

    return len(decoded) == 32


def _validate_sdp(label: str, sdp: Any, expected_type: str) -> None:
    if not isinstance(sdp, dict):
        raise ValueError(f"{label} must be a JSON object")

    if sdp.get("type") != expected_type:
        raise ValueError(f"{label}.type must equal {expected_type!r}")

    if not isinstance(sdp.get("sdp"), str) or not sdp["sdp"].strip():
        raise ValueError(f"{label}.sdp must be a non-empty string")


def _validate_message_metadata(metadata: Any) -> Dict[str, Any]:
    if not isinstance(metadata, dict):
        raise ValueError("message_metadata must be a JSON object")

    for required in ("message_id", "sender_key_id"):
        if not isinstance(metadata.get(required), str) or not metadata[required].strip():
            raise ValueError(f"message_metadata.{required} must be a non-empty string")

    sender_key = metadata.get("sender_key")
    if sender_key is not None and not isinstance(sender_key, str):
        raise ValueError("message_metadata.sender_key must be a string when present")

    topology_hints = metadata.get("topology_hints")
    if topology_hints is not None:
        if not isinstance(topology_hints, list) or any(
            not isinstance(h, str) or not h.strip() for h in topology_hints
        ):
            raise ValueError(
                "message_metadata.topology_hints must be a list of non-empty strings"
            )

    return metadata


def _validate_chunk_announcements(chunk_announcements: Any) -> BlackoutSignalValidationResult:
    if chunk_announcements is None:
        return BlackoutSignalValidationResult()

    if not isinstance(chunk_announcements, list):
        raise ValueError("chunk_announcements must be a list")

    missing_redundancy_metadata = False
    invalid_redundancy_metadata = False
    for idx, chunk in enumerate(chunk_announcements):
        prefix = f"chunk_announcements[{idx}]"
        if not isinstance(chunk, dict):
            raise ValueError(f"{prefix} must be a JSON object")

        if not isinstance(chunk.get("chunk_id"), str) or not chunk["chunk_id"].strip():
            raise ValueError(f"{prefix}.chunk_id must be a non-empty string")

        if not _is_fixed_length_hash(chunk.get("chunk_hash")):
            raise ValueError(
                f"{prefix}.chunk_hash must be a fixed-length hex/base64 hash"
            )

        merkle_root = chunk.get("merkle_root")
        if merkle_root is not None and not _is_fixed_length_hash(merkle_root):
            raise ValueError(
                f"{prefix}.merkle_root must be a fixed-length hex/base64 hash"
            )

        replication_factor = chunk.get("replication_factor")
        replica_hints = chunk.get("replica_hints")
        if replication_factor is None:
            missing_redundancy_metadata = True
        else:
            if not isinstance(replication_factor, int) or not (1 <= replication_factor <= 10):
                raise ValueError(
                    f"{prefix}.replication_factor must be an integer between 1 and 10"
                )

        if replica_hints is not None:
            if not isinstance(replica_hints, list) or len(replica_hints) > 20:
                raise ValueError(
                    f"{prefix}.replica_hints must be a list with at most 20 entries"
                )
            if any(not isinstance(hint, str) or not hint.strip() for hint in replica_hints):
                raise ValueError(
                    f"{prefix}.replica_hints must contain non-empty string entries"
                )

        if isinstance(replication_factor, int) and isinstance(replica_hints, list):
            if len(replica_hints) < replication_factor:
                invalid_redundancy_metadata = True

    return BlackoutSignalValidationResult(
        missing_redundancy_metadata=missing_redundancy_metadata,
        invalid_redundancy_metadata=invalid_redundancy_metadata,
    )


def validate_blackout_signal_content(content: Any) -> BlackoutSignalValidationResult:
    if not isinstance(content, dict):
        raise ValueError("m.blackout.signal content must be a JSON object")

    allowed_keys = {
        "ice_candidates",
        "sdp_offer",
        "sdp_answer",
        "message_metadata",
        "chunk_announcements",
        "offline_retrieval",
        "self_destruct_after",
    }

    unknown = set(content) - allowed_keys
    if unknown:
        raise ValueError(
            "m.blackout.signal content contains unsupported fields: %s"
            % ", ".join(sorted(unknown))
        )

    ice_candidates = content.get("ice_candidates")
    if ice_candidates is not None:
        if not isinstance(ice_candidates, list):
            raise ValueError("ice_candidates must be a list of candidate objects")

        for idx, candidate in enumerate(ice_candidates):
            if not isinstance(candidate, dict):
                raise ValueError("ice_candidates must be a list of candidate objects")

            prefix = f"ice_candidates[{idx}]"
            if not isinstance(candidate.get("candidate"), str) or not candidate[
                "candidate"
            ].strip():
                raise ValueError(f"{prefix}.candidate must be a non-empty string")

            sdp_m_line_index = candidate.get("sdpMLineIndex")
            if sdp_m_line_index is not None and not isinstance(sdp_m_line_index, int):
                raise ValueError(f"{prefix}.sdpMLineIndex must be an integer")

            sdp_mid = candidate.get("sdpMid")
            if sdp_mid is not None and not isinstance(sdp_mid, str):
                raise ValueError(f"{prefix}.sdpMid must be a string")

    if "sdp_offer" in content:
        _validate_sdp("sdp_offer", content.get("sdp_offer"), expected_type="offer")

    if "sdp_answer" in content:
        _validate_sdp("sdp_answer", content.get("sdp_answer"), expected_type="answer")

    _validate_message_metadata(content.get("message_metadata"))

    offline_retrieval = content.get("offline_retrieval")
    if offline_retrieval is not None:
        if not isinstance(offline_retrieval, dict):
            raise ValueError("offline_retrieval must be a JSON object")
        if not isinstance(offline_retrieval.get("manifest_id"), str):
            raise ValueError("offline_retrieval.manifest_id must be a string")
        if not isinstance(offline_retrieval.get("external_fetch_required"), bool):
            raise ValueError(
                "offline_retrieval.external_fetch_required must be a boolean"
            )

    return _validate_chunk_announcements(content.get("chunk_announcements"))


def extract_sender_key_identifiers_from_signal_content(content: Any) -> List[str]:
    if not isinstance(content, dict):
        return []

    message_metadata = content.get("message_metadata")
    if not isinstance(message_metadata, dict):
        return []

    key_identifiers: List[str] = []
    sender_key_id = message_metadata.get("sender_key_id")
    sender_key = message_metadata.get("sender_key")

    if isinstance(sender_key_id, str):
        key_identifiers.append(sender_key_id)
    if isinstance(sender_key, str):
        key_identifiers.append(sender_key)

    return key_identifiers
