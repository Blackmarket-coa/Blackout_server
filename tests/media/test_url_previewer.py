# Copyright 2023 The Matrix.org Foundation C.I.C.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import datetime
import os
from unittest import mock

from twisted.test.proto_helpers import MemoryReactor

from synapse.server import HomeServer
from synapse.api.errors import SynapseError
from synapse.types import UserID
from synapse.util import Clock

from tests import unittest
from tests.unittest import override_config

try:
    import lxml
except ImportError:
    lxml = None  # type: ignore[assignment]


class URLPreviewTests(unittest.HomeserverTestCase):
    if not lxml:
        skip = "url preview feature requires lxml"

    def make_homeserver(self, reactor: MemoryReactor, clock: Clock) -> HomeServer:
        config = self.default_config()
        config["url_preview_enabled"] = True
        config["max_spider_size"] = 9999999
        config["url_preview_ip_range_blacklist"] = (
            "192.168.1.1",
            "1.0.0.0/8",
            "3fff:ffff:ffff:ffff:ffff:ffff:ffff:ffff",
            "2001:800::/21",
        )

        self.storage_path = self.mktemp()
        self.media_store_path = self.mktemp()
        os.mkdir(self.storage_path)
        os.mkdir(self.media_store_path)
        config["media_store_path"] = self.media_store_path

        provider_config = {
            "module": "synapse.media.storage_provider.FileStorageProviderBackend",
            "store_local": True,
            "store_synchronous": False,
            "store_remote": True,
            "config": {"directory": self.storage_path},
        }

        config["media_storage_providers"] = [provider_config]

        return self.setup_test_homeserver(config=config)

    def prepare(self, reactor: MemoryReactor, clock: Clock, hs: HomeServer) -> None:
        media_repo = hs.get_media_repository()
        assert media_repo.url_previewer is not None
        self.url_previewer = media_repo.url_previewer

    def test_all_urls_allowed(self) -> None:
        self.assertFalse(self.url_previewer._is_url_blocked("http://matrix.org"))
        self.assertFalse(self.url_previewer._is_url_blocked("https://matrix.org"))
        self.assertFalse(self.url_previewer._is_url_blocked("http://localhost:8000"))
        self.assertFalse(
            self.url_previewer._is_url_blocked("http://user:pass@matrix.org")
        )

    @override_config(
        {
            "url_preview_url_blacklist": [
                {"username": "user"},
                {"scheme": "http", "netloc": "matrix.org"},
            ]
        }
    )
    def test_blocked_url(self) -> None:
        # Blocked via scheme and URL.
        self.assertTrue(self.url_previewer._is_url_blocked("http://matrix.org"))
        # Not blocked because all components must match.
        self.assertFalse(self.url_previewer._is_url_blocked("https://matrix.org"))

        # Blocked due to the user.
        self.assertTrue(
            self.url_previewer._is_url_blocked("http://user:pass@example.com")
        )
        self.assertTrue(self.url_previewer._is_url_blocked("http://user@example.com"))

    @override_config({"url_preview_url_blacklist": [{"netloc": "*.example.com"}]})
    def test_glob_blocked_url(self) -> None:
        # All subdomains are blocked.
        self.assertTrue(self.url_previewer._is_url_blocked("http://foo.example.com"))
        self.assertTrue(self.url_previewer._is_url_blocked("http://.example.com"))

        # The TLD is not blocked.
        self.assertFalse(self.url_previewer._is_url_blocked("https://example.com"))

    @override_config({"url_preview_url_blacklist": [{"netloc": "^.+\\.example\\.com"}]})
    def test_regex_blocked_urL(self) -> None:
        # All subdomains are blocked.
        self.assertTrue(self.url_previewer._is_url_blocked("http://foo.example.com"))
        # Requires a non-empty subdomain.
        self.assertFalse(self.url_previewer._is_url_blocked("http://.example.com"))

        # The TLD is not blocked.
        self.assertFalse(self.url_previewer._is_url_blocked("https://example.com"))


    def test_get_expiration_ms_prefers_cache_control(self) -> None:
        headers = {
            b"Cache-Control": [b"public, max-age=120"],
            b"Expires": [b"Wed, 21 Oct 2030 07:28:00 GMT"],
        }

        self.assertEqual(self.url_previewer._get_expiration_ms(headers), 120000)

    def test_get_expiration_ms_uses_expires_header(self) -> None:
        now_s = self.clock.time_msec() // 1000
        expires = now_s + 90

        with mock.patch("synapse.media.url_previewer.parsedate_to_datetime") as parse_dt:
            parse_dt.return_value = datetime.datetime.fromtimestamp(
                expires, tz=datetime.timezone.utc
            )
            headers = {b"Expires": [b"ignored by patched parser"]}
            expiration_ms = self.url_previewer._get_expiration_ms(headers)

        self.assertGreaterEqual(expiration_ms, 89000)
        self.assertLessEqual(expiration_ms, 90000)

    def test_handle_url_cleans_up_file_on_store_failure(self) -> None:
        def fail_store_local_media(**kwargs: object) -> object:
            raise SynapseError(500, "boom")

        with mock.patch(
            "synapse.media.url_previewer.random_string", return_value="abcdefghijklmnop"
        ), mock.patch.object(
            self.url_previewer,
            "_download_url",
            new=mock.AsyncMock(
                return_value=mock.Mock(
                    media_type="text/plain",
                    length=3,
                    download_name=None,
                    uri="http://example.com",
                    response_code=200,
                    expires=1000,
                    etag=None,
                )
            ),
        ), mock.patch.object(
            self.url_previewer.store,
            "store_local_media",
            side_effect=fail_store_local_media,
        ):
            with self.assertRaises(SynapseError):
                self.get_success(
                    self.url_previewer._handle_url(
                        "http://example.com", UserID.from_string("@user:test")
                    )
                )

        media_id = f"{datetime.date.today().isoformat()}_abcdefghijklmnop"
        self.assertFalse(
            os.path.exists(self.url_previewer.filepaths.url_cache_filepath(media_id))
        )
