# SPDX-License-Identifier: Apache-2.0
"""Loopback static file server used by the audit."""

from __future__ import annotations

import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def _handler_for(root: Path):
    root_resolved = root.resolve()

    class Handler(SimpleHTTPRequestHandler):
        server_version = "sitekit-audit/0.1"

        def __init__(self, *args, **kwargs):  # noqa: D401 - stdlib signature
            super().__init__(*args, directory=str(root_resolved), **kwargs)

        def log_message(self, format, *args):  # noqa: A002 - stdlib signature
            """Keep test output quiet."""

        def _allowed_request(self):
            expected = f"127.0.0.1:{self.server.server_port}"
            host = self.headers.get("Host", "")
            origin = self.headers.get("Origin")
            return host == expected and (origin is None or origin == f"http://{expected}")

        def do_GET(self):
            if not self._allowed_request():
                self.send_error(403)
                return
            super().do_GET()

        def do_HEAD(self):
            if not self._allowed_request():
                self.send_error(403)
                return
            super().do_HEAD()

        def send_head(self):
            resolved = Path(super().translate_path(self.path)).resolve()
            if resolved != root_resolved and root_resolved not in resolved.parents:
                self.send_error(404)
                return None
            return super().send_head()

    return Handler


class SiteServer:
    """Serve a built site on 127.0.0.1 with a random free port."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "SiteServer":
        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), _handler_for(self.root))
        self._httpd.daemon_threads = True
        self._thread = threading.Thread(
            target=self._httpd.serve_forever, name="sitekit-audit-http", daemon=True
        )
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._httpd = None
        self._thread = None

    @property
    def host(self) -> str:
        if self._httpd is None:
            raise RuntimeError("server is not running")
        return str(self._httpd.server_address[0])

    @property
    def port(self) -> int:
        if self._httpd is None:
            raise RuntimeError("server is not running")
        return int(self._httpd.server_address[1])

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"
