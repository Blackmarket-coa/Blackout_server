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

    def create_resource_dict(self):
        BlackoutRuntimeModule({"persistence_path": "/tmp/blackout_runtime_e2e.sqlite3"}, self.hs.get_module_api())
        resources = super().create_resource_dict()
        resources.update(self.hs._module_web_resources)
        return resources

    def prepare(self, reactor, clock, hs):
        self.user_id = self.register_user("alice", "pass")
        self.tok = self.login("alice", "pass")

    def test_governance_and_reputation_synapse_api_endpoints_live(self) -> None:
        room_id = self.helper.create_room_as(
            self.user_id,
            tok=self.tok,
            is_public=False,
            extra_content={"creation_content": {"m.blackout.channel.type": "governance"}},
        )

        vote = self.make_request(
            "PUT",
            f"/_matrix/client/v3/rooms/{room_id}/send/m.blackout.governance.vote/1",
            {"proposal_id": "p1", "vote": "yes", "decision": "accepted"},
            access_token=self.tok,
        )
        self.assertEqual(vote.code, 200, vote.result)

        decisions = self.make_request(
            "GET",
            f"/_synapse/client/blackout/governance/decisions?room_id={room_id}&since=0",
            access_token=self.tok,
        )
        self.assertEqual(decisions.code, 200, decisions.result)
        self.assertEqual(decisions.json_body["decisions"][0]["decision"], "accepted")

        rep = self.make_request(
            "PUT",
            f"/_matrix/client/v3/rooms/{room_id}/send/m.blackout.reputation.update/2",
            {"node_id": "node-1", "delta": 2, "reason": "delivery_success", "rating": 4},
            access_token=self.tok,
        )
        self.assertEqual(rep.code, 200, rep.result)

        reputation = self.make_request(
            "GET",
            "/_synapse/client/blackout/reputation/node-1",
            access_token=self.tok,
        )
        self.assertEqual(reputation.code, 200, reputation.result)
        self.assertEqual(reputation.json_body["node_id"], "node-1")

    def test_vote_uniqueness_and_rate_limiting(self) -> None:
        room_id = self.helper.create_room_as(
            self.user_id,
            tok=self.tok,
            is_public=False,
            extra_content={"creation_content": {"m.blackout.channel.type": "governance"}},
        )

        first_vote = self.make_request(
            "PUT",
            f"/_matrix/client/v3/rooms/{room_id}/send/m.blackout.governance.vote/10",
            {"proposal_id": "p2", "vote": "yes", "decision": "accepted"},
            access_token=self.tok,
        )
        self.assertEqual(first_vote.code, 200, first_vote.result)

        second_vote = self.make_request(
            "PUT",
            f"/_matrix/client/v3/rooms/{room_id}/send/m.blackout.governance.vote/11",
            {"proposal_id": "p2", "vote": "no"},
            access_token=self.tok,
        )
        self.assertEqual(second_vote.code, 403, second_vote.result)
