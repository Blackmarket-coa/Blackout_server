from __future__ import annotations

from synapse.rest import admin
from synapse.rest.client import login, register, room

from blackout_runtime.module import BlackoutRuntimeModule
from tests.unittest import HomeserverTestCase


class BlackoutRuntimeModuleE2ETestCase(HomeserverTestCase):
    servlets = [
        admin.register_servlets,
        login.register_servlets,
        register.register_servlets,
        room.register_servlets,
    ]

    def prepare(self, reactor, clock, hs):
        BlackoutRuntimeModule({}, hs.get_module_api())
        self.user_id = self.register_user("alice", "pass")
        self.tok = self.login("alice", "pass")

    def test_create_room_template_and_event_policy_enforced(self) -> None:
        room_id = self.helper.create_room_as(
            self.user_id,
            tok=self.tok,
            is_public=False,
            extra_content={"creation_content": {"m.blackout.channel.type": "governance"}},
        )

        join_rules = self.make_request(
            "GET",
            f"/_matrix/client/v3/rooms/{room_id}/state/m.room.join_rules",
            access_token=self.tok,
        )
        self.assertEqual(join_rules.code, 200, join_rules.result)
        self.assertEqual(join_rules.json_body["join_rule"], "invite")

        unauth = self.make_request(
            "PUT",
            f"/_matrix/client/v3/rooms/{room_id}/send/m.blackout.governance.proposal/1",
            {"proposal_id": "missing_fields"},
        )
        self.assertEqual(unauth.code, 401, unauth.result)

        bad_event = self.make_request(
            "PUT",
            f"/_matrix/client/v3/rooms/{room_id}/send/m.blackout.governance.proposal/2",
            {"proposal_id": "missing_fields"},
            access_token=self.tok,
        )
        self.assertEqual(bad_event.code, 403, bad_event.result)

    def test_send_event_rules_enforced_end_to_end(self) -> None:
        room_id = self.helper.create_room_as(
            self.user_id,
            tok=self.tok,
            is_public=False,
            extra_content={"creation_content": {"m.blackout.channel.type": "governance"}},
        )

        ok_vote = self.make_request(
            "PUT",
            f"/_matrix/client/v3/rooms/{room_id}/send/m.blackout.governance.vote/3",
            {
                "proposal_id": "p1",
                "vote": "yes",
                "decision": "accepted",
            },
            access_token=self.tok,
        )
        self.assertEqual(ok_vote.code, 200, ok_vote.result)

        bad_reputation = self.make_request(
            "PUT",
            f"/_matrix/client/v3/rooms/{room_id}/send/m.blackout.reputation.update/4",
            {
                "node_id": "node-1",
                "delta": "bad",
                "reason": "delivery_success",
            },
            access_token=self.tok,
        )
        self.assertEqual(bad_reputation.code, 403, bad_reputation.result)
