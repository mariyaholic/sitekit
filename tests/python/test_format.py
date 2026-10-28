# SPDX-License-Identifier: Apache-2.0
from scripts.check_format import problems


def test_whitespace_checks():
    assert problems(b"good\n") == []
    assert problems(b"\tbad \r\nlast") == [
        "missing final newline", "non-LF line ending",
        "line 1: trailing whitespace", "line 1: tab indentation",
    ]
