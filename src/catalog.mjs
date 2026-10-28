// SPDX-License-Identifier: Apache-2.0

import { SitekitError } from "./errors.mjs";

export const STATUS_LABELS = Object.freeze({
  open: "Open",
  closed: "Closed",
  planned: "Planned",
});

export const ROOM_ID_PATTERN = /^[a-z0-9][a-z0-9-]*$/;

/**
 * @param {string} status
 * @returns {string}
 */
export function statusLabel(status) {
  return STATUS_LABELS[status] ?? status;
}

/**
 * Fixed room illustration path, see docs/CONTRACT.md.
 * @param {string} roomId
 * @returns {string}
 */
export function roomAssetPath(roomId) {
  return `assets/rooms/${roomId}.svg`;
}

function nonEmptyString(value) {
  return typeof value === "string" && value.trim() !== "";
}

/**
 * Validate catalog rules that the schema subset cannot express.
 *
 * @param {unknown} catalog
 * @returns {object} the same catalog, for chaining
 * @throws {SitekitError} with one detail line per problem
 */
export function parseCatalog(catalog) {
  const problems = [];

  if (typeof catalog !== "object" || catalog === null || Array.isArray(catalog)) {
    throw new SitekitError("catalog must be a JSON object", {
      details: ["/ : expected object"],
    });
  }

  const site = catalog.site;
  if (typeof site !== "object" || site === null || Array.isArray(site)) {
    problems.push("/site : expected object");
  } else {
    for (const field of ["title", "tagline", "description"]) {
      if (!nonEmptyString(site[field])) {
        problems.push(`/site/${field} : expected a non-empty string`);
      }
    }
  }

  if (!Array.isArray(catalog.rooms)) {
    problems.push("/rooms : expected array");
  } else if (catalog.rooms.length === 0) {
    problems.push("/rooms : expected at least one room");
  } else {
    const seenRooms = new Set();
    catalog.rooms.forEach((room, index) => {
      const base = `/rooms/${index}`;
      if (typeof room !== "object" || room === null || Array.isArray(room)) {
        problems.push(`${base} : expected object`);
        return;
      }
      if (typeof room.id !== "string" || !ROOM_ID_PATTERN.test(room.id)) {
        problems.push(`${base}/id : expected a slug matching ${ROOM_ID_PATTERN}`);
      } else if (seenRooms.has(room.id)) {
        problems.push(`${base}/id : duplicate room id "${room.id}"`);
      } else {
        seenRooms.add(room.id);
      }
      for (const field of ["name", "summary"]) {
        if (!nonEmptyString(room[field])) {
          problems.push(`${base}/${field} : expected a non-empty string`);
        }
      }
      if (!Object.hasOwn(STATUS_LABELS, room.status)) {
        problems.push(
          `${base}/status : expected one of ${Object.keys(STATUS_LABELS).join(", ")}`,
        );
      }
      if (!Array.isArray(room.tags)) {
        problems.push(`${base}/tags : expected array`);
      } else {
        room.tags.forEach((tag, tagIndex) => {
          if (!nonEmptyString(tag)) {
            problems.push(`${base}/tags/${tagIndex} : expected a non-empty string`);
          }
        });
      }
      if (!Array.isArray(room.items)) {
        problems.push(`${base}/items : expected array`);
      } else if (room.items.length === 0) {
        problems.push(`${base}/items : expected at least one item`);
      } else {
        const seenItems = new Set();
        room.items.forEach((item, itemIndex) => {
          const itemBase = `${base}/items/${itemIndex}`;
          if (typeof item !== "object" || item === null || Array.isArray(item)) {
            problems.push(`${itemBase} : expected object`);
            return;
          }
          if (typeof item.id !== "string" || !ROOM_ID_PATTERN.test(item.id)) {
            problems.push(
              `${itemBase}/id : expected a slug matching ${ROOM_ID_PATTERN}`,
            );
          } else if (seenItems.has(item.id)) {
            problems.push(`${itemBase}/id : duplicate item id "${item.id}"`);
          } else {
            seenItems.add(item.id);
          }
          if (!nonEmptyString(item.label)) {
            problems.push(`${itemBase}/label : expected a non-empty string`);
          }
          if (Object.hasOwn(item, "note") && !nonEmptyString(item.note)) {
            problems.push(`${itemBase}/note : expected a non-empty string`);
          }
        });
      }
    });
  }

  if (problems.length > 0) {
    throw new SitekitError("catalog does not satisfy the sitekit contract", {
      details: problems,
    });
  }
  return catalog;
}
