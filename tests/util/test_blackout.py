from synapse.util.blackout import validate_blackout_signal_content

from tests import unittest


class BlackoutSignalSchemaValidationTestCase(unittest.TestCase):
    def test_rejects_missing_message_metadata(self) -> None:
        with self.assertRaises(ValueError):
            validate_blackout_signal_content({"sdp_offer": {"type": "offer", "sdp": "v=0"}})

    def test_rejects_unknown_fields(self) -> None:
        with self.assertRaises(ValueError):
            validate_blackout_signal_content(
                {
                    "message_metadata": {
                        "message_id": "m1",
                        "sender_key_id": "ed25519:dev1",
                    },
                    "unknown": "value",
                }
            )

    def test_accepts_valid_signal_payload(self) -> None:
        validate_blackout_signal_content(
            {
                "message_metadata": {
                    "message_id": "m1",
                    "sender_key_id": "ed25519:dev1",
                    "topology_hints": ["relay:a"],
                },
                "sdp_offer": {"type": "offer", "sdp": "v=0"},
                "chunk_announcements": [
                    {
                        "chunk_id": "chunk-1",
                        "chunk_hash": "a" * 64,
                        "replication_factor": 1,
                        "replica_hints": ["peer-1"],
                    }
                ],
            }
        )
