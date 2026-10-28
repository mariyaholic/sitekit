# SPDX-License-Identifier: Apache-2.0
"""Loopback static file server used by the audit."""

from __future__ import annotations

import os
import stat
import threading
from urllib.parse import unquote, urlsplit
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def _open_contained(root: Path, request_path: str):
    """Open a regular file without following path components outside root."""
    parts = unquote(urlsplit(request_path).path).split("/")
    parts = [part for part in parts if part not in ("", ".")]
    if any(part == ".." or "\\" in part or "\x00" in part for part in parts):
        raise OSError("invalid path")
    if not parts or request_path.split("?", 1)[0].endswith("/"):
        parts.append("index.html")
    if os.name == "nt":
        # Check the final path of the open handle, not the mutable pathname.
        import ctypes
        import msvcrt
        from ctypes import wintypes

        file = open(root.joinpath(*parts), "rb")
        try:
            get_path = ctypes.windll.kernel32.GetFinalPathNameByHandleW
            get_path.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
            get_path.restype = wintypes.DWORD
            handle = msvcrt.get_osfhandle(file.fileno())
            size = get_path(handle, None, 0, 0)
            if not size:
                raise OSError("cannot resolve opened file")
            buffer = ctypes.create_unicode_buffer(size + 1)
            if not get_path(handle, buffer, len(buffer), 0):
                raise OSError("cannot resolve opened file")
            actual = Path(buffer.value).resolve()
            if not actual.is_relative_to(root.resolve()) or not stat.S_ISREG(os.fstat(file.fileno()).st_mode):
                raise OSError("file outside root")
            return file
        except BaseException:
            file.close()
            raise
    flags = os.O_RDONLY | os.O_NOFOLLOW
    directory = os.open(root.anchor, flags | os.O_DIRECTORY)
    try:
        for part in (*root.parts[1:], *parts[:-1]):
            next_directory = os.open(part, flags | os.O_DIRECTORY, dir_fd=directory)
            os.close(directory)
            directory = next_directory
        fd = os.open(parts[-1], flags | os.O_NONBLOCK, dir_fd=directory)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise OSError("not a regular file")
            return os.fdopen(fd, "rb")
        except BaseException:
            os.close(fd)
            raise
    finally:
        os.close(directory)


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
            try:
                file = _open_contained(root_resolved, self.path)
            except (OSError, ValueError):
                self.send_error(404)
                return None
            try:
                info = os.fstat(file.fileno())
                self.send_response(200)
                self.send_header("Content-type", self.guess_type(self.path.split("?", 1)[0]))
                self.send_header("Content-Length", str(info.st_size))
                self.send_header("Last-Modified", self.date_time_string(info.st_mtime))
                self.end_headers()
                return file
            except BaseException:
                file.close()
                raise

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
