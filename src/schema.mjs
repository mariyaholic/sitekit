// SPDX-License-Identifier: Apache-2.0

/**
 * A deliberately small JSON Schema subset validator.
 *
 * Six validating keywords are supported: type, properties, required, items,
 * enum and additionalProperties. Annotation keywords are ignored. Every other
 * keyword is reported so callers cannot mistake this for full JSON Schema.
 */

export const VALIDATING_KEYWORDS = Object.freeze([
  "type",
  "enum",
  "required",
  "properties",
  "items",
  "additionalProperties",
]);

export const ANNOTATION_KEYWORDS = Object.freeze([
  "$schema",
  "$id",
  "$comment",
  "title",
  "description",
  "default",
]);

const ANNOTATIONS = new Set(ANNOTATION_KEYWORDS);
const VALIDATING = new Set(VALIDATING_KEYWORDS);
const TYPES = new Set([
  "object",
  "array",
  "string",
  "number",
  "integer",
  "boolean",
  "null",
]);

function isPlainObject(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function pointer(base, segment) {
  const safe = String(segment).replace(/~/g, "~0").replace(/\//g, "~1");
  return `${base}/${safe}`;
}

function canonicalJson(value) {
  if (Array.isArray(value)) {
    return `[${value.map(canonicalJson).join(",")}]`;
  }
  if (isPlainObject(value)) {
    const keys = Object.keys(value).sort();
    return `{${keys.map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function typeMatches(value, type) {
  switch (type) {
    case "object":
      return isPlainObject(value);
    case "array":
      return Array.isArray(value);
    case "string":
      return typeof value === "string";
    case "number":
      return typeof value === "number" && Number.isFinite(value);
    case "integer":
      return typeof value === "number" && Number.isInteger(value);
    case "boolean":
      return typeof value === "boolean";
    case "null":
      return value === null;
    default:
      return false;
  }
}

function describeType(type) {
  return Array.isArray(type) ? type.join(" or ") : type;
}

/**
 * Validate one schema node against a document value.
 * @param {unknown} schema
 * @param {unknown} value
 * @param {string} path JSON pointer of the value.
 * @param {{errors: object[], warnings: object[], warnUnsupported: boolean}} state
 */
function validateNode(schema, value, path, state) {
  if (!isPlainObject(schema)) {
    state.errors.push({
      path,
      keyword: "schema",
      message: "schema node must be an object",
    });
    return;
  }

  for (const key of Object.keys(schema)) {
    if (ANNOTATIONS.has(key)) {
      continue;
    }
    if (!VALIDATING.has(key)) {
      const entry = {
        path: pointer(path, key),
        keyword: key,
        message:
          `unsupported schema keyword "${key}"; sitekit validates only ` +
          VALIDATING_KEYWORDS.join(", "),
      };
      if (state.warnUnsupported) {
        state.warnings.push(entry);
      } else {
        state.errors.push(entry);
      }
    }
  }

  let typeMismatch = false;
  if (Object.hasOwn(schema, "type")) {
    const declared = schema.type;
    const declaredTypes = Array.isArray(declared) ? declared : [declared];
    if (
      declaredTypes.length === 0 ||
      declaredTypes.some((type) => typeof type !== "string" || !TYPES.has(type))
    ) {
      state.errors.push({
        path: pointer(path, "type"),
        keyword: "type",
        message: `invalid type declaration ${JSON.stringify(declared)}`,
      });
      return;
    }
    if (!declaredTypes.some((type) => typeMatches(value, type))) {
      state.errors.push({
        path,
        keyword: "type",
        message: `expected ${describeType(declared)}, received ${describeValue(value)}`,
      });
      typeMismatch = true;
    }
  }

  if (Object.hasOwn(schema, "enum")) {
    const allowed = schema.enum;
    if (!Array.isArray(allowed) || allowed.length === 0) {
      state.errors.push({
        path: pointer(path, "enum"),
        keyword: "enum",
        message: "enum must be a non-empty array",
      });
    } else {
      const serialised = canonicalJson(value);
      if (!allowed.some((candidate) => canonicalJson(candidate) === serialised)) {
        state.errors.push({
          path,
          keyword: "enum",
          message: `expected one of ${allowed.map((item) => JSON.stringify(item)).join(", ")}, received ${JSON.stringify(value)}`,
        });
      }
    }
  }

  const objectValue = isPlainObject(value);
  const arrayValue = Array.isArray(value);

  if (Object.hasOwn(schema, "required")) {
    const required = schema.required;
    if (
      !Array.isArray(required) ||
      required.some((member) => typeof member !== "string")
    ) {
      state.errors.push({
        path: pointer(path, "required"),
        keyword: "required",
        message: "required must be an array of property names",
      });
    } else if (objectValue) {
      for (const member of required) {
        if (!Object.hasOwn(value, member)) {
          state.errors.push({
            path,
            keyword: "required",
            message: `missing required property "${member}"`,
          });
        }
      }
    }
  }

  if (Object.hasOwn(schema, "properties")) {
    const properties = schema.properties;
    if (!isPlainObject(properties)) {
      state.errors.push({
        path: pointer(path, "properties"),
        keyword: "properties",
        message: "properties must be an object of schemas",
      });
    } else if (objectValue && !typeMismatch) {
      for (const [name, subschema] of Object.entries(properties)) {
        if (Object.hasOwn(value, name)) {
          validateNode(subschema, value[name], pointer(path, name), state);
        }
      }
    }
  }

  if (Object.hasOwn(schema, "items")) {
    if (!isPlainObject(schema.items)) {
      state.errors.push({
        path: pointer(path, "items"),
        keyword: "items",
        message: "items must be a single schema object (tuple form is not supported)",
      });
    } else if (arrayValue && !typeMismatch) {
      value.forEach((element, index) => {
        validateNode(schema.items, element, pointer(path, index), state);
      });
    }
  }

  if (Object.hasOwn(schema, "additionalProperties")) {
    const additional = schema.additionalProperties;
    if (typeof additional !== "boolean") {
      state.errors.push({
        path: pointer(path, "additionalProperties"),
        keyword: "additionalProperties",
        message: "additionalProperties must be true or false",
      });
    } else if (additional === false && objectValue) {
      const declared = isPlainObject(schema.properties)
        ? new Set(Object.keys(schema.properties))
        : new Set();
      for (const key of Object.keys(value)) {
        if (!declared.has(key)) {
          state.errors.push({
            path: pointer(path, key),
            keyword: "additionalProperties",
            message: `unexpected property "${key}"`,
          });
        }
      }
    }
  }
}

function describeValue(value) {
  if (Array.isArray(value)) {
    return "array";
  }
  if (value === null) {
    return "null";
  }
  if (typeof value === "number" && Number.isInteger(value)) {
    return "integer";
  }
  return typeof value;
}

/**
 * @param {unknown} schema
 * @param {unknown} document
 * @param {{warnUnsupported?: boolean}} [options]
 * @returns {{valid: boolean, errors: object[], warnings: object[]}}
 */
export function validate(schema, document, { warnUnsupported = false } = {}) {
  const state = { errors: [], warnings: [], warnUnsupported };
  validateNode(schema, document, "", state);
  return { valid: state.errors.length === 0, errors: state.errors, warnings: state.warnings };
}

/**
 * Render one validation result as `path: message` lines.
 * @param {object[]} entries
 * @returns {string[]}
 */
export function formatIssues(entries) {
  return entries.map((entry) => `${entry.path === "" ? "/" : entry.path}: ${entry.message}`);
}
