"""Services for the babybuddy integration."""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID, ATTR_ID
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_set_service_schema
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .client import get_datetime_from_time
from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

    from .coordinator import BabyBuddyCoordinator

# ---------------------------------------------------------------------------
# Helpers shared with the old code (kept with string literals)
# ---------------------------------------------------------------------------


async def _async_extract_entry_coordinator(
    call: ServiceCall,
) -> BabyBuddyCoordinator:
    """Extract coordinator from a service call."""
    entry = None
    for entry in call.hass.config_entries.async_loaded_entries(DOMAIN):
        if entry.state is not ConfigEntryState.LOADED:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="entry_not_loaded",
            )
    if not entry:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="entry_not_loaded",
        )
    return entry.runtime_data.coordinator


def _build_entity_id_to_child_map(
    coordinator: BabyBuddyCoordinator,
) -> dict[str, int]:
    """Build a mapping of known entity_id patterns to child IDs."""
    mapping: dict[str, int] = {}
    for child in coordinator.data[0]:
        child_id = child[ATTR_ID]
        device_slug = slugify(f'{child["first_name"]} {child["last_name"]}')
        mapping[f"sensor.{device_slug}"] = child_id
        mapping[f"switch.{device_slug}_timer"] = child_id
    return mapping


async def _setup_service_data(
    call: ServiceCall, coordinator: BabyBuddyCoordinator
) -> dict[str, Any]:
    """Extract data with child ID from a service call."""
    data = call.data.copy()
    entity_map = _build_entity_id_to_child_map(coordinator)

    # Resolve child from explicit "child" entity_id field
    if isinstance(data.get("child"), str) and data["child"].startswith(
        ("sensor.", "switch.")
    ):
        resolved = entity_map.get(data["child"])
        if resolved is not None:
            data["child"] = resolved

    # Resolve child from HA target (entity_id)
    if not isinstance(data.get("child"), int) and call.data.get(ATTR_ENTITY_ID):
        target_id = call.data[ATTR_ENTITY_ID]
        if isinstance(target_id, list):
            target_id = target_id[0]
        # Match target entity to a child by checking if entity_id starts with device slug
        for child in coordinator.data[0]:
            device_slug = slugify(f'{child["first_name"]} {child["last_name"]}')
            entity_slug = target_id.split(".", 1)[1] if "." in target_id else target_id
            if entity_slug == device_slug or entity_slug.startswith(f"{device_slug}_"):
                data["child"] = child[ATTR_ID]
                break

    # Resolve timer if requested
    if data.get("timer") and isinstance(data.get("child"), int):
        child_id = data["child"]
        timer_data = coordinator.data[1].get(child_id, {}).get("timers", {})
        if timer_data:
            data["timer"] = [timer_data[ATTR_ID]]
        else:
            del data["timer"]

    return data


async def _set_common_fields(
    call: ServiceCall, data: dict[str, Any], coordinator: BabyBuddyCoordinator
) -> dict[str, Any]:
    """Set data common fields."""

    if data.get("timer"):
        child_id = data["child"]
        timer_data = coordinator.data[1].get(child_id, {}).get("timers", {})
        if not timer_data:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="timer_not_found",
            )
        data["timer"] = timer_data[ATTR_ID]
    else:
        data["start"] = get_datetime_from_time(
            call.data.get("start") or dt_util.now()
        )
        data["end"] = get_datetime_from_time(
            call.data.get("end") or dt_util.now()
        )

    if call.data.get("tags"):
        data["tags"] = call.data.get("tags")

    return data


# ---------------------------------------------------------------------------
# Schema / description builders (driven by discovery v2 metadata)
# ---------------------------------------------------------------------------

_TYPE_TO_VALIDATOR: dict[str, Any] = {
    "string": cv.string,
    "float": cv.positive_float,
    "int": cv.positive_int,
    "boolean": cv.boolean,
    "date": cv.date,
    "datetime": vol.Any(cv.datetime, cv.time),
    "time": cv.time,
    "entity_id": cv.entity_id,
    "string_list": vol.All(cv.ensure_list, [str]),
}


def _get_select_options(select_key: str, metadata: dict) -> list[str]:
    """Look up select options by key from metadata."""
    for s in metadata.get("selects", []):
        if s["key"] == select_key:
            return s.get("options", [])
    return []


def _get_vol_validator(field_def: dict, metadata: dict) -> Any:  # noqa: ANN401
    """Map a discovery field type to a voluptuous validator."""
    ftype = field_def["type"]
    if ftype == "select":
        options = _get_select_options(field_def["select_key"], metadata)
        return vol.In(options)
    return _TYPE_TO_VALIDATOR.get(ftype, cv.string)


_BASE_SELECTORS: dict[str, dict] = {
    "boolean": {"boolean": {}},
    "date": {"text": {}},
    "datetime": {"time": {}},
    "time": {"time": {}},
    "string_list": {"text": {"multiple": True}},
}


def _get_selector(field_def: dict, metadata: dict) -> dict:
    """Build an HA selector dict from a BB field definition."""
    ftype = field_def["type"]

    # Simple static selectors
    if ftype in _BASE_SELECTORS:
        return _BASE_SELECTORS[ftype]

    # String: check multiline hint
    if ftype == "string":
        return {"text": {"multiline": True}} if field_def.get("multiline") else {"text": {}}

    # Number types: merge BB selector_hints
    if ftype in ("float", "int"):
        return {"number": {"mode": "box", **field_def.get("selector_hints", {})}}

    # Select: look up options from metadata
    if ftype == "select":
        return {"select": {"options": _get_select_options(field_def["select_key"], metadata)}}

    # Entity: use BB-provided domain
    if ftype == "entity_id":
        return {"entity": {"integration": DOMAIN, "domain": field_def.get("entity_domain", "sensor")}}

    return {"text": {}}


def _build_schema(svc_def: dict, metadata: dict) -> vol.Schema:
    """Build a vol.Schema for validation from a service definition."""
    fields: dict = {}

    if svc_def.get("common_fields"):
        fields[vol.Optional("child")] = cv.entity_id
        fields[vol.Optional("notes")] = cv.string
        fields[vol.Optional("tags")] = vol.All(cv.ensure_list, [str])

    if svc_def.get("uses_timer"):
        fields[vol.Optional("child")] = cv.entity_id
        fields[vol.Exclusive("timer", group_of_exclusion="timer_or_start")] = (
            cv.boolean
        )
        fields[
            vol.Exclusive("start", group_of_exclusion="timer_or_start")
        ] = vol.Any(cv.datetime, cv.time)
        fields[vol.Optional("end")] = vol.Any(cv.datetime, cv.time)
        fields[vol.Optional("tags")] = vol.All(cv.ensure_list, [str])

    for fname, fdef in svc_def.get("fields", {}).items():
        # Skip fields already added by common_fields / uses_timer
        already = {k.schema if hasattr(k, "schema") else k for k in fields}
        if fname in already:
            continue

        validator = _get_vol_validator(fdef, metadata)
        # entity_id fields can be resolved from HA target, so always optional
        if fdef.get("required") and fdef["type"] != "entity_id":
            fields[vol.Required(fname)] = validator
        else:
            fields[vol.Optional(fname)] = validator

    # Accept entity_id from HA target resolution
    fields[vol.Optional(ATTR_ENTITY_ID)] = vol.Any(cv.entity_id, [cv.entity_id])

    return vol.Schema(fields)


def _build_service_description(svc_def: dict, metadata: dict) -> dict:
    """Build a service description dict for async_set_service_schema."""
    fields: dict = {}

    if svc_def.get("common_fields"):
        fields["child"] = {
            "name": "Child",
            "required": True,
            "selector": {
                "entity": {
                    "integration": DOMAIN,
                    "domain": "sensor",
                    "device_class": "babybuddy_child",
                }
            },
        }
        fields["notes"] = {
            "name": "Notes",
            "selector": {"text": {"multiline": True}},
        }
        fields["tags"] = {
            "name": "Tags",
            "selector": {"text": {"multiple": True}},
        }

    if svc_def.get("uses_timer"):
        fields["child"] = {
            "name": "Child",
            "required": True,
            "selector": {"entity": {"integration": DOMAIN, "domain": "switch"}},
        }
        fields["timer"] = {
            "name": "Use timer",
            "selector": {"boolean": {}},
        }
        fields["start"] = {
            "name": "Start time",
            "selector": {"time": {}},
        }
        fields["end"] = {
            "name": "End time",
            "selector": {"time": {}},
        }
        fields["tags"] = {
            "name": "Tags",
            "selector": {"text": {"multiple": True}},
        }

    for fname, fdef in svc_def.get("fields", {}).items():
        if fname in fields:
            continue
        field_desc: dict[str, Any] = {
            "name": fdef["name"],
            "selector": _get_selector(fdef, metadata),
        }
        if fdef.get("description"):
            field_desc["description"] = fdef["description"]
        if fdef.get("required"):
            field_desc["required"] = True
        fields[fname] = field_desc

    return {
        "name": svc_def["name"],
        "description": svc_def["description"],
        "fields": fields,
    }


# ---------------------------------------------------------------------------
# Transform applier
# ---------------------------------------------------------------------------


def _apply_transforms(
    data: dict[str, Any], svc_def: dict, metadata: dict
) -> None:
    """Apply transforms defined in the service definition to data in-place."""
    transforms_map = metadata.get("transforms", {})

    for field_name, transform_key in svc_def.get("transforms", {}).items():
        if field_name not in data or data[field_name] is None:
            continue

        transform = transforms_map.get(transform_key)
        if not transform:
            continue

        if transform["type"] == "mapping":
            value = data[field_name]
            mapping = transform.get("mapping", {})
            mapped = mapping.get(value)
            if mapped:
                data.update(mapped)
                if transform.get("removes_field"):
                    del data[field_name]

        elif transform["type"] == "value_transform":
            if transform.get("operation") == "lowercase":
                data[field_name] = data[field_name].lower()


# ---------------------------------------------------------------------------
# Generic service handler
# ---------------------------------------------------------------------------


async def _async_handle_service(
    call: ServiceCall, svc_def: dict, metadata: dict
) -> None:
    """Generic handler for all Baby Buddy services."""
    coordinator = await _async_extract_entry_coordinator(call)

    # Special case: DELETE method (delete_last_entry)
    if svc_def.get("method") == "DELETE":
        entity_id = call.data.get(ATTR_ENTITY_ID)
        entity = call.hass.states.get(entity_id) if entity_id else None
        if not entity:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="entry_not_loaded",
            )
        parts = entity_id.split(".")
        if len(parts) < 2:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="entry_not_loaded",
            )
        slug_parts = parts[1].split("_")
        if len(slug_parts) < 4:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="entry_not_loaded",
            )
        key = slug_parts[3]
        entry_id = entity.attributes.get(ATTR_ID)
        if entry_id is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="entry_not_loaded",
            )
        await coordinator.client.async_delete(key, entry_id)
        await coordinator.async_request_refresh()
        return

    data = await _setup_service_data(call, coordinator)

    # Timer-based services need common fields
    if svc_def.get("uses_timer"):
        data = await _set_common_fields(call, data, coordinator)

    # Apply datetime conversions for datetime-type fields
    for fname, fdef in svc_def.get("fields", {}).items():
        if fdef["type"] == "datetime" and fname in data and data[fname] is not None:
            data[fname] = get_datetime_from_time(data[fname])

    # Apply transforms (e.g. diaper type -> wet/solid booleans, lowercase)
    _apply_transforms(data, svc_def, metadata)

    # Handle extra_data mappings (e.g. schedule_id -> medication_schedule)
    for target_field, mapping in svc_def.get("extra_data", {}).items():
        source_field = mapping.get("from_field")
        if source_field and source_field in data:
            data[target_field] = data.pop(source_field)

    # POST to the endpoint
    date_time_now = get_datetime_from_time(dt_util.now())
    await coordinator.client.async_post(svc_def["endpoint"], data, date_time_now)
    await coordinator.async_request_refresh()


# ---------------------------------------------------------------------------
# Service registration (called from __init__.py async_setup_entry)
# ---------------------------------------------------------------------------


async def async_setup_services(
    hass: HomeAssistant, coordinator: BabyBuddyCoordinator
) -> None:
    """Register all services dynamically from discovery metadata."""
    metadata = coordinator.metadata

    for svc in metadata.get("services", []):
        key = svc["key"]
        if hass.services.has_service(DOMAIN, key):
            continue

        # Build validation schema and register handler
        schema = _build_schema(svc, metadata)
        hass.services.async_register(
            DOMAIN,
            key,
            functools.partial(_async_handle_service, svc_def=svc, metadata=metadata),
            schema=schema,
        )

        # Build and set UI description programmatically
        description = _build_service_description(svc, metadata)
        async_set_service_schema(hass, DOMAIN, key, description)

    LOGGER.info("Registered %d Baby Buddy services", len(metadata.get("services", [])))
