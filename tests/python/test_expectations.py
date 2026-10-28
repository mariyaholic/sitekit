# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json

import pytest

from sitekit_audit.expectations import (
    ExpectationError,
    from_catalog,
    load_expectations,
)


def clone(catalog):
    return json.loads(json.dumps(catalog))


def test_derives_expectations_from_the_example(example_catalog, repo_root):
    site = from_catalog(example_catalog)
    assert site.title == "Atrium Rooms"
    rooms = {room.id: room for room in site.rooms}
    assert list(rooms) == ["studio", "library", "workshop", "garden"]
    assert rooms["studio"].status == "open"
    assert rooms["studio"].status_label == "Open"
    assert rooms["workshop"].status_label == "Planned"
    assert rooms["garden"].asset == "assets/rooms/garden.svg"
    assert [item.id for item in rooms["library"].items] == ["reading-chair", "atlas-case", "index"]
    assert rooms["studio"].tags == ("writing", "daylight")


def test_loads_from_disk(repo_root):
    site = load_expectations(repo_root / "examples" / "room-catalog" / "catalog.json")
    assert len(site.rooms) == 4


def test_missing_catalog_is_reported(scratch_factory):
    with pytest.raises(ExpectationError, match="cannot read catalog"):
        load_expectations(scratch_factory() / "absent.json")


def test_malformed_catalog_is_reported(scratch_factory):
    path = scratch_factory() / "catalog.json"
    path.write_text("{nope", encoding="utf-8")
    with pytest.raises(ExpectationError, match="cannot parse catalog"):
        load_expectations(path)


def test_rejects_a_non_object_catalog():
    with pytest.raises(ExpectationError, match="must be a JSON object"):
        from_catalog([])


def test_rejects_duplicate_room_ids(example_catalog):
    catalog = clone(example_catalog)
    catalog["rooms"][1]["id"] = catalog["rooms"][0]["id"]
    with pytest.raises(ExpectationError, match="duplicate room id"):
        from_catalog(catalog)


def test_rejects_a_room_without_items(example_catalog):
    catalog = clone(example_catalog)
    catalog["rooms"][0]["items"] = []
    with pytest.raises(ExpectationError, match="items: expected a non-empty array"):
        from_catalog(catalog)


def test_rejects_duplicate_item_ids(example_catalog):
    catalog = clone(example_catalog)
    catalog["rooms"][0]["items"][1]["id"] = catalog["rooms"][0]["items"][0]["id"]
    with pytest.raises(ExpectationError, match="duplicate item id"):
        from_catalog(catalog)


def test_rejects_unknown_status(example_catalog):
    catalog = clone(example_catalog)
    catalog["rooms"][0]["status"] = "draft"
    with pytest.raises(ExpectationError, match="status: expected one of"):
        from_catalog(catalog)


def test_rejects_empty_strings_and_bad_notes(example_catalog):
    catalog = clone(example_catalog)
    catalog["site"]["title"] = " "
    with pytest.raises(ExpectationError, match="site/title"):
        from_catalog(catalog)

    catalog = clone(example_catalog)
    catalog["rooms"][0]["items"][0]["note"] = 4
    with pytest.raises(ExpectationError, match="note: expected a non-empty string"):
        from_catalog(catalog)


@pytest.mark.parametrize("status", [[], {}, None])
def test_rejects_non_string_status(example_catalog, status):
    catalog = clone(example_catalog)
    catalog["rooms"][0]["status"] = status
    with pytest.raises(ExpectationError, match="status: expected one of"):
        from_catalog(catalog)


def test_rejects_slug_with_trailing_newline(example_catalog):
    catalog = clone(example_catalog)
    catalog["rooms"][0]["id"] += "\n"
    with pytest.raises(ExpectationError, match="expected a slug"):
        from_catalog(catalog)
