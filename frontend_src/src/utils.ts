import type {
  HomeAssistant,
  EntityRegistryEntry,
  ChildEntities,
} from "./types";

declare const CARD_VERSION: string;

export function getVersion(): string {
  return CARD_VERSION;
}

export function timeSince(isoDate: string): string {
  const then = new Date(isoDate).getTime();
  const now = Date.now();
  const diffMs = now - then;

  if (diffMs < 0) return "just now";

  const minutes = Math.floor(diffMs / 60_000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 0) return `${days}d ${hours % 24}h ago`;
  if (hours > 0) return `${hours}h ${minutes % 60}m ago`;
  if (minutes > 0) return `${minutes}m ago`;
  return "just now";
}

export function childAge(birthDate: string): string {
  const birth = new Date(birthDate);
  const now = new Date();

  let months =
    (now.getFullYear() - birth.getFullYear()) * 12 +
    (now.getMonth() - birth.getMonth());
  if (now.getDate() < birth.getDate()) months--;

  if (months < 1) {
    const days = Math.floor(
      (now.getTime() - birth.getTime()) / 86_400_000,
    );
    return `${days} day${days !== 1 ? "s" : ""} old`;
  }
  if (months < 24) {
    return `${months} month${months !== 1 ? "s" : ""} old`;
  }
  const years = Math.floor(months / 12);
  const rem = months % 12;
  if (rem === 0) return `${years} year${years !== 1 ? "s" : ""} old`;
  return `${years}y ${rem}m old`;
}

export function discoverChildEntities(
  entityId: string,
  hass: HomeAssistant,
  entityRegistry: EntityRegistryEntry[],
): ChildEntities {
  const result: ChildEntities = {
    primary: null,
    sensors: [],
    timers: [],
    startTimerButton: null,
    binarySensors: [],
    selects: [],
  };

  const entry = entityRegistry.find((e) => e.entity_id === entityId);
  if (!entry?.device_id) {
    result.primary = hass.states[entityId] ?? null;
    return result;
  }

  const deviceId = entry.device_id;
  const siblings = entityRegistry.filter(
    (e) => e.device_id === deviceId && e.platform === "babybuddy",
  );

  for (const sib of siblings) {
    const state = hass.states[sib.entity_id];
    if (!state) continue;

    const eid = sib.entity_id;

    if (eid === entityId) {
      result.primary = state;
    } else if (
      eid.startsWith("button.") &&
      eid.endsWith("_start_timer")
    ) {
      result.startTimerButton = state;
    } else if (
      eid.startsWith("sensor.") &&
      state.attributes.timer_id != null
    ) {
      result.timers.push(state);
    } else if (eid.startsWith("binary_sensor.")) {
      result.binarySensors.push(state);
    } else if (eid.startsWith("select.")) {
      result.selects.push(state);
    } else if (eid.startsWith("sensor.")) {
      result.sensors.push(state);
    }
  }

  return result;
}

/**
 * Extract the activity key from an entity_id by stripping the child name prefix.
 * e.g. ("sensor.alice_test_last_feeding", "alice_test") => "last_feeding"
 */
export function extractActivityKey(
  entityId: string,
  childPrefix: string,
): string {
  const name = entityId.split(".")[1] ?? entityId;
  const prefix = childPrefix + "_";
  if (name.startsWith(prefix)) return name.slice(prefix.length);
  return name;
}

/**
 * Look up an entity's icon from the entity registry.
 * Falls back to a provided default if the entity isn't found or has no icon.
 */
export function resolveIcon(
  entityId: string,
  registry: EntityRegistryEntry[],
  fallback = "mdi:help-circle",
): string {
  const entry = registry.find((e) => e.entity_id === entityId);
  return entry?.original_icon ?? fallback;
}

/**
 * Build a keyword → icon map from Baby Buddy sensor entities in the registry.
 * Useful for mapping service keys to icons (services don't have icons,
 * but their keywords overlap with sensor entity names).
 */
export function buildKeywordIconMap(
  registry: EntityRegistryEntry[],
): Record<string, string> {
  const map: Record<string, string> = {};
  for (const entry of registry) {
    if (entry.platform !== "babybuddy" || !entry.original_icon) continue;
    if (!entry.entity_id.startsWith("sensor.")) continue;
    const name = entry.entity_id.split(".")[1] ?? "";
    const parts = name.split("_");
    for (const part of parts) {
      if (part && !map[part]) {
        map[part] = entry.original_icon;
      }
    }
  }
  return map;
}

/**
 * Resolve an icon for a service key by matching keywords against
 * a keyword-to-icon map built from the entity registry.
 */
export function resolveServiceIcon(
  serviceKey: string,
  keywordIconMap: Record<string, string>,
  fallback = "mdi:plus-circle",
): string {
  const parts = serviceKey.split("_");
  for (const part of parts) {
    if (part && keywordIconMap[part]) return keywordIconMap[part];
  }
  return fallback;
}

export function labelForServiceKey(key: string): string {
  return key
    .replace(/^add_/, "")
    .replace(/^give_/, "")
    .replace(/[-_]/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

/** @deprecated Use {@link labelForServiceKey} instead. */
export const activityLabel = labelForServiceKey;
