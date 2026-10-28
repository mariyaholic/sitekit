# SPDX-License-Identifier: Apache-2.0
"""Catalog-derived expectations for the generated page."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

STATUS_LABELS = {"open": "Open", "closed": "Closed", "planned": "Planned"}
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class ExpectationError(Exception):
    """Raised when the catalog cannot describe an auditable page."""


@dataclass(frozen=True)
class ItemExpectation:
    id: str
    label: str
    note: str | None


@dataclass(frozen=True)
class RoomExpectation:
    id: str
    name: str
    status: str
    status_label: str
    summary: str
    tags: tuple[str, ...]
    items: tuple[ItemExpectation, ...]

    @property
    def asset(self) -> str:
        return f"assets/rooms/{self.id}.svg"


@dataclass(frozen=True)
class SiteExpectation:
    title: str
    tagline: str
    description: str
    rooms: tuple[RoomExpectation, ...]


def _text(value: object, path: str, problems: list[str]) -> str:
    if not isinstance(value, str) or value.strip() == "":
        problems.append(f"{path}: expected a non-empty string")
        return ""
    return value


def from_catalog(data: object) -> SiteExpectation:
    """Build expectations, raising ExpectationError with every problem found."""
    problems: list[str] = []
    if not isinstance(data, dict):
        raise ExpectationError("catalog must be a JSON object")

    site = data.get("site")
    if not isinstance(site, dict):
        raise ExpectationError("catalog/site must be a JSON object")
    title = _text(site.get("title"), "site/title", problems)
    tagline = _text(site.get("tagline"), "site/tagline", problems)
    description = _text(site.get("description"), "site/description", problems)

    rooms_data = data.get("rooms")
    rooms: list[RoomExpectation] = []
    if not isinstance(rooms_data, list) or not rooms_data:
        raise ExpectationError("catalog/rooms must be a non-empty array")

    seen_rooms: set[str] = set()
    for index, room in enumerate(rooms_data):
        base = f"rooms/{index}"
        if not isinstance(room, dict):
            problems.append(f"{base}: expected an object")
            continue
        room_id = room.get("id")
        if not isinstance(room_id, str) or not SLUG.fullmatch(room_id):
            problems.append(f"{base}/id: expected a slug")
            continue
        if room_id in seen_rooms:
            problems.append(f"{base}/id: duplicate room id {room_id!r}")
            continue
        seen_rooms.add(room_id)

        status = room.get("status")
        if not isinstance(status, str) or status not in STATUS_LABELS:
            problems.append(f"{base}/status: expected one of {', '.join(STATUS_LABELS)}")
            status_label = ""
        else:
            status_label = STATUS_LABELS[status]

        tags_data = room.get("tags")
        tags: list[str] = []
        if not isinstance(tags_data, list):
            problems.append(f"{base}/tags: expected an array")
        else:
            for tag_index, tag in enumerate(tags_data):
                tags.append(_text(tag, f"{base}/tags/{tag_index}", problems))

        items_data = room.get("items")
        items: list[ItemExpectation] = []
        if not isinstance(items_data, list) or not items_data:
            problems.append(f"{base}/items: expected a non-empty array")
        else:
            seen_items: set[str] = set()
            for item_index, item in enumerate(items_data):
                item_base = f"{base}/items/{item_index}"
                if not isinstance(item, dict):
                    problems.append(f"{item_base}: expected an object")
                    continue
                item_id = item.get("id")
                if not isinstance(item_id, str) or not SLUG.fullmatch(item_id):
                    problems.append(f"{item_base}/id: expected a slug")
                    continue
                if item_id in seen_items:
                    problems.append(f"{item_base}/id: duplicate item id {item_id!r}")
                    continue
                seen_items.add(item_id)
                label = _text(item.get("label"), f"{item_base}/label", problems)
                note = item.get("note")
                if note is not None and (not isinstance(note, str) or note.strip() == ""):
                    problems.append(f"{item_base}/note: expected a non-empty string")
                    note = None
                items.append(ItemExpectation(item_id, label, note))

        rooms.append(
            RoomExpectation(
                id=room_id,
                name=_text(room.get("name"), f"{base}/name", problems),
                status=status if isinstance(status, str) else "",
                status_label=status_label,
                summary=_text(room.get("summary"), f"{base}/summary", problems),
                tags=tuple(tags),
                items=tuple(items),
            )
        )

    if problems:
        raise ExpectationError(
            "catalog does not satisfy the sitekit contract:\n  " + "\n  ".join(problems)
        )
    return SiteExpectation(
        title=title,
        tagline=tagline,
        description=description,
        rooms=tuple(rooms),
    )


def load_expectations(path: str | Path) -> SiteExpectation:
    """Read and parse a catalog file."""
    catalog_path = Path(path)
    try:
        text = catalog_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ExpectationError(f"cannot read catalog {catalog_path}: {error}") from error
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        raise ExpectationError(f"cannot parse catalog {catalog_path}: {error}") from error
    return from_catalog(data)
