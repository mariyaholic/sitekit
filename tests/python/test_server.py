# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import http.client
import urllib.error
import urllib.request

import pytest

from sitekit_audit.server import SiteServer


def fetch(server: SiteServer, path: str):
    with urllib.request.urlopen(server.base_url + path, timeout=5) as response:
        return response.status, response.headers, response.read()


def test_serves_the_built_site_on_loopback(built_site):
    with SiteServer(built_site) as server:
        assert server.host == "127.0.0.1"
        assert server.port > 0
        status, headers, body = fetch(server, "/index.html")
        assert status == 200
        assert b"Atrium Rooms" in body
        assert headers.get_content_type() == "text/html"


def test_serves_assets_with_the_right_content_type(built_site):
    with SiteServer(built_site) as server:
        status, headers, body = fetch(server, "/assets/site.css")
        assert status == 200
        assert headers.get_content_type() == "text/css"
        assert b"--sk-color-ink" in body

        status, headers, _ = fetch(server, "/assets/rooms/studio.svg")
        assert status == 200
        assert headers.get_content_type() == "image/svg+xml"


def test_missing_file_returns_404(built_site):
    with SiteServer(built_site) as server:
        with pytest.raises(urllib.error.HTTPError) as error:
            fetch(server, "/missing.html")
        assert error.value.code == 404


def test_cannot_escape_the_served_root(built_site, scratch_factory):
    secret = built_site.parent / "secret.txt"
    secret.write_text("do not serve", encoding="utf-8")
    with SiteServer(built_site) as server:
        connection = http.client.HTTPConnection(server.host, server.port, timeout=5)
        try:
            connection.request("GET", "/../secret.txt")
            response = connection.getresponse()
            body = response.read().decode("utf-8", "replace")
        finally:
            connection.close()
        assert response.status in {403, 404}
        assert "do not serve" not in body


def test_server_stops_after_the_context(built_site):
    with SiteServer(built_site) as server:
        base_url = server.base_url
    with pytest.raises(urllib.error.URLError):
        urllib.request.urlopen(base_url + "/index.html", timeout=2)
