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
from .const import ACTIVE_TIMERS_KEY, DOMAIN, LOGGER
from .entity import child_device_name

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant, ServiceCall

    from .coordinator import BabyBuddyCoordinator

# ---------------------------------------------------------------------------
# Service call data helpers
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
    for child in coordinator.data.children:
        child_id = child[ATTR_ID]
        device_slug = slugify(child_device_name(child, coordinator.metadata))
        mapping[f"sensor.{device_slug}"] = child_id
        mapping[f"button.{device_slug}_start_timer"] = child_id
    return mapping


async def _setup_service_data(
    call: ServiceCall, coordinator: BabyBuddyCoordinator
) -> dict[str, Any]:
    """Extract data with child ID from a service call."""
    data = call.data.copy()
    entity_map = _build_entity_id_to_child_map(coordinator)

    # Resolve child from explicit "child" entity_id field
    if isinstance(data.get("child"), str) and data["child"].startswith(
        ("sensor.", "button.")
    ):
        resolved = entity_map.get(data["child"])
        if resolved is not None:
            data["child"] = resolved

    # Resolve child from HA target (entity_id)
    if not isinstance(data.get("child"), int) and call.data.get(ATTR_ENTITY_ID):
        target_id = call.data[ATTR_ENTITY_ID]
        if isinstance(target_id, list):
            target_id = target_id[0]
        for child in coordinator.data.children:
            device_slug = slugify(child_device_name(child, coordinator.metadata))
            entity_slug = target_id.split(".", 1)[1] if "." in target_id else target_id
            if entity_slug == device_slug or entity_slug.startswith(f"{device_slug}_"):
                data["child"] = child[ATTR_ID]
                break

    # Resolve timer: explicit int IDs are trusted (BB API validates);
    # non-int truthy values (e.g. True) resolve to the first cached timer.
    # Note: bool is a subclass of int in Python, so check bool first.
    if data.get("timer") and isinstance(data.get("child"), int):
        child_id = data["child"]
        timer_val = data["timer"]
        if isinstance(timer_val, int) and not isinstance(timer_val, bool):
            data["timer"] = timer_val
        else:
            timers = coordinator.data.child_data.get(child_id, {}).get(
                ACTIVE_TIMERS_KEY, []
            )
            if timers:
                data["timer"] = timers[0][ATTR_ID]
            else:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="timer_not_found",
                )

    return data


def _apply_defaults(data: dict[str, Any], svc_def: dict) -> None:
    """Apply metadata-driven defaults, respecting exclusion groups."""
    fields = svc_def.get("fields", {})

    exc_groups: dict[str, list[str]] = {}
    for fname, fdef in fields.items():
        group = fdef.get("exclusion_group")
        if group:
            exc_groups.setdefault(group, []).append(fname)

    for fname, fdef in fields.items():
        if fname in data and data[fname] is not None:
            continue

        default = fdef.get("default")
        if not default:
            continue

        group = fdef.get("exclusion_group")
        if group:
            siblings = exc_groups.get(group, [])
            if any(s != fname and data.get(s) is not None for s in siblings):
                continue

        if default == "now":
            data[fname] = dt_util.now()
        elif default == "today":
            data[fname] = dt_util.now().strftime("%Y-%m-%d")


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
    "child_entity": cv.entity_id,
    "timer": vol.Any(cv.boolean, cv.positive_int),
    "string_list": vol.All(cv.ensure_list, [str]),
}


def _get_select_options(select_key: str, metadata: dict) -> list:
    """Look up select options by key from metadata.

    Prefers ``options_detail`` (rich objects with value/label/color) when
    available, falling back to the flat ``options`` list.
    """
    for s in metadata.get("selects", []):
        if s["key"] == select_key:
            if s.get("options_detail"):
                return s["options_detail"]
            return s.get("options", [])
    return []


def _extract_option_values(options: list) -> list[str]:
    """Return plain string values from a mixed options list."""
    return [o["value"] if isinstance(o, dict) else o for o in options]


def _get_vol_validator(field_def: dict, metadata: dict) -> Any:  # noqa: ANN401
    """Map a discovery field type to a voluptuous validator."""
    ftype = field_def["type"]
    if ftype == "select":
        options = _get_select_options(field_def["select_key"], metadata)
        return vol.In(_extract_option_values(options))
    return _TYPE_TO_VALIDATOR.get(ftype, cv.string)


_BASE_SELECTORS: dict[str, dict] = {
    "boolean": {"boolean": {}},
    "date": {"date": {}},
    "datetime": {"time": {}},
    "time": {"time": {}},
    "string_list": {"text": {"multiple": True}},
    "child_entity": {
        "entity": {
            "integration": DOMAIN,
            "domain": "sensor",
            "device_class": "babybuddy_child",
        }
    },
    "timer": {"number": {"mode": "box", "min": 1}},
}


def _get_selector(field_def: dict, metadata: dict) -> dict:
    """Build an HA selector dict from a BB field definition."""
    ftype = field_def["type"]

    if ftype in _BASE_SELECTORS:
        return _BASE_SELECTORS[ftype]

    if ftype == "string":
        return (
            {"text": {"multiline": True}}
            if field_def.get("multiline")
            else {"text": {}}
        )

    if ftype in ("float", "int"):
        return {"number": {"mode": "box", **field_def.get("selector_hints", {})}}

    if ftype == "select":
        return {
            "select": {
                "options": _get_select_options(field_def["select_key"], metadata)
            }
        }

    if ftype == "entity_id":
        return {
            "entity": {
                "integration": DOMAIN,
                "domain": field_def.get("entity_domain", "sensor"),
            }
        }

    return {"text": {}}


def _build_schema(svc_def: dict, metadata: dict) -> vol.Schema:
    """Build a vol.Schema for validation from a service definition."""
    fields: dict = {}

    for fname, fdef in svc_def.get("fields", {}).items():
        validator = _get_vol_validator(fdef, metadata)
        ftype = fdef["type"]

        exc_group = fdef.get("exclusion_group")
        if exc_group:
            key = vol.Exclusive(fname, group_of_exclusion=exc_group)
        elif fdef.get("required") and ftype not in ("entity_id", "child_entity"):
            key = vol.Required(fname)
        else:
            key = vol.Optional(fname)

        fields[key] = validator

    # Accept entity_id from HA target resolution
    fields[vol.Optional(ATTR_ENTITY_ID)] = vol.Any(cv.entity_id, [cv.entity_id])

    return vol.Schema(fields)


def _build_service_description(svc_def: dict, metadata: dict) -> dict:
    """Build a service description dict for async_set_service_schema."""
    fields: dict = {}

    for fname, fdef in svc_def.get("fields", {}).items():
        field_desc: dict[str, Any] = {
            "_order": fdef.get("order", 50),
            "name": fdef["name"],
            "selector": _get_selector(fdef, metadata),
        }
        if fdef.get("default"):
            field_desc["default"] = fdef["default"]
        if fdef.get("description"):
            field_desc["description"] = fdef["description"]
        if fdef.get("required"):
            field_desc["required"] = True
        if fdef.get("hidden_in_card"):
            field_desc["hidden_in_card"] = True
        if fdef.get("exclusion_group"):
            field_desc["exclusion_group"] = fdef["exclusion_group"]
        if fdef.get("hidden_when_group"):
            field_desc["hidden_when_group"] = fdef["hidden_when_group"]
        fields[fname] = field_desc

    sorted_fields = dict(
        sorted(fields.items(), key=lambda item: item[1].pop("_order", 50))
    )
    return {
        "name": svc_def["name"],
        "description": svc_def["description"],
        "fields": sorted_fields,
    }


# ---------------------------------------------------------------------------
# Transform applier
# ---------------------------------------------------------------------------


def _apply_transforms(data: dict[str, Any], svc_def: dict, metadata: dict) -> None:
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
        entity_slug = parts[1]
        key = None
        for desc in coordinator.sensor_descriptions:
            suffix = f"_{desc.key.replace('-', '_')}"
            if entity_slug.endswith(suffix):
                key = desc.key
                break
        if key is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="entry_not_loaded",
            )
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

    _apply_defaults(data, svc_def)

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

    # Strip HA-internal fields before posting to BB
    data.pop(ATTR_ENTITY_ID, None)

    # POST to the endpoint
    date_time_now = get_datetime_from_time(dt_util.now())
    await coordinator.client.async_post(svc_def["endpoint"], data, date_time_now)
    await coordinator.async_request_refresh()


# ---------------------------------------------------------------------------
# Service registration (called from __init__.py async_setup_entry)
# ---------------------------------------------------------------------------


async def async_setup_services(
    hass: HomeAssistant, coordinator: BabyBuddyCoordinator
) -> list[str]:
    """Register all services dynamically from discovery metadata.

    Returns the list of service keys that were registered so the caller
    can unregister them on entry unload.
    """
    metadata = coordinator.metadata
    registered: list[str] = []

    for svc in metadata.get("services", []):
        key = svc["key"]
        if hass.services.has_service(DOMAIN, key):
            registered.append(key)
            continue

        # Build validation schema and register handler
        schema = _build_schema(svc, metadata)
        hass.services.async_register(
            DOMAIN,
            key,
            functools.partial(_async_handle_service, svc_def=svc, metadata=metadata),
            schema=schema,
        )

        registered.append(key)

        # Build and set UI description programmatically
        description = _build_service_description(svc, metadata)
        async_set_service_schema(hass, DOMAIN, key, description)

    # ---- Manual timer management services ----

    if not hass.services.has_service(DOMAIN, "start_timer"):
        start_timer_schema = vol.Schema(
            {
                vol.Required("child"): cv.entity_id,
                vol.Optional("name"): cv.string,
                vol.Optional(ATTR_ENTITY_ID): vol.Any(cv.entity_id, [cv.entity_id]),
            }
        )

        async def _async_handle_start_timer(call: ServiceCall) -> None:
            coord = await _async_extract_entry_coordinator(call)
            data = await _setup_service_data(call, coord)
            if not isinstance(data.get("child"), int):
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="entry_not_loaded",
                )
            post_data: dict[str, Any] = {
                "child": data["child"],
                "start": get_datetime_from_time(dt_util.now()),
            }
            if data.get("name"):
                post_data["name"] = data["name"]
            timer_meta = coord.metadata.get("timer", {})
            endpoint = timer_meta.get("endpoint", "timers")
            await coord.client.async_post(endpoint, post_data)
            await coord.async_request_refresh()

        hass.services.async_register(
            DOMAIN, "start_timer", _async_handle_start_timer, start_timer_schema
        )
        async_set_service_schema(
            hass,
            DOMAIN,
            "start_timer",
            {
                "name": "Start timer",
                "description": "Start a new timer for a child.",
                "fields": {
                    "child": {
                        "name": "Child",
                        "required": True,
                        "selector": {
                            "entity": {
                                "integration": DOMAIN,
                                "domain": "sensor",
                                "device_class": "babybuddy_child",
                            }
                        },
                    },
                    "name": {
                        "name": "Timer name",
                        "description": "Optional name for the timer.",
                        "selector": {"text": {}},
                    },
                },
            },
        )

    if not hass.services.has_service(DOMAIN, "stop_timer"):
        stop_timer_schema = vol.Schema(
            {
                vol.Required("timer_id"): cv.positive_int,
            }
        )

        async def _async_handle_stop_timer(call: ServiceCall) -> None:
            coord = await _async_extract_entry_coordinator(call)
            timer_id = call.data["timer_id"]
            timer_meta = coord.metadata.get("timer", {})
            endpoint = timer_meta.get("endpoint", "timers")
            await coord.client.async_delete(endpoint, timer_id)
            await coord.async_request_refresh()

        hass.services.async_register(
            DOMAIN, "stop_timer", _async_handle_stop_timer, stop_timer_schema
        )
        async_set_service_schema(
            hass,
            DOMAIN,
            "stop_timer",
            {
                "name": "Stop timer",
                "description": "Delete (cancel) an active timer by its ID.",
                "fields": {
                    "timer_id": {
                        "name": "Timer ID",
                        "required": True,
                        "description": "The Baby Buddy timer ID to stop.",
                        "selector": {"number": {"mode": "box", "min": 1}},
                    },
                },
            },
        )

    if not hass.services.has_service(DOMAIN, "rename_timer"):
        rename_timer_schema = vol.Schema(
            {
                vol.Required("timer_id"): cv.positive_int,
                vol.Required("name"): cv.string,
            }
        )

        async def _async_handle_rename_timer(call: ServiceCall) -> None:
            coord = await _async_extract_entry_coordinator(call)
            timer_id = call.data["timer_id"]
            name = call.data["name"]
            timer_meta = coord.metadata.get("timer", {})
            endpoint = timer_meta.get("endpoint", "timers")
            await coord.client.async_patch(endpoint, timer_id, {"name": name})
            await coord.async_request_refresh()

        hass.services.async_register(
            DOMAIN, "rename_timer", _async_handle_rename_timer, rename_timer_schema
        )
        async_set_service_schema(
            hass,
            DOMAIN,
            "rename_timer",
            {
                "name": "Rename timer",
                "description": "Rename an active timer.",
                "fields": {
                    "timer_id": {
                        "name": "Timer ID",
                        "required": True,
                        "description": "The Baby Buddy timer ID to rename.",
                        "selector": {"number": {"mode": "box", "min": 1}},
                    },
                    "name": {
                        "name": "Name",
                        "required": True,
                        "description": "New name for the timer.",
                        "selector": {"text": {}},
                    },
                },
            },
        )

    registered.extend(["start_timer", "stop_timer", "rename_timer"])
    LOGGER.info("Registered %d Baby Buddy services", len(registered))
    return registered
