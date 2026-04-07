export interface BabyBuddyCardConfig {
  type: string;
  entity?: string;
  show_timer?: boolean;
  show_actions?: boolean;
  compact?: boolean;
}

export interface HomeAssistant {
  states: Record<string, HassEntity>;
  services: Record<string, Record<string, HassService>>;
  callService(
    domain: string,
    service: string,
    data?: Record<string, unknown>,
  ): Promise<void>;
  callWS<T>(message: Record<string, unknown>): Promise<T>;
  formatEntityState(stateObj: HassEntity, state?: string): string;
  formatEntityAttributeValue(
    stateObj: HassEntity,
    attribute: string,
    value?: unknown,
  ): string;
  formatEntityAttributeName(
    stateObj: HassEntity,
    attribute: string,
  ): string;
  connection: {
    sendMessagePromise(message: Record<string, unknown>): Promise<unknown>;
    subscribeEvents(
      callback: (event: Record<string, unknown>) => void,
      eventType: string,
    ): Promise<() => void>;
  };
  language: string;
  locale: Record<string, unknown>;
}

export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
  last_changed: string;
  last_updated: string;
  context: { id: string; user_id: string | null };
}

export interface HassService {
  name?: string;
  description?: string;
  fields?: Record<string, HassServiceField>;
  target?: Record<string, unknown>;
}

export interface HassServiceField {
  name?: string;
  description?: string;
  required?: boolean;
  example?: unknown;
  selector?: Record<string, unknown>;
}

export interface EntityRegistryEntry {
  entity_id: string;
  device_id: string | null;
  platform: string;
  translation_key: string | null;
  original_name: string | null;
  original_icon: string | null;
  unique_id: string;
}

export interface DeviceRegistryEntry {
  id: string;
  name: string | null;
  name_by_user: string | null;
}

export interface ChildEntities {
  primary: HassEntity | null;
  sensors: HassEntity[];
  timers: HassEntity[];
  startTimerButton: HassEntity | null;
  binarySensors: HassEntity[];
  selects: HassEntity[];
}

export interface BbActionDetail {
  action: string;
}

export interface BbTimerStopDetail {
  action: string;
  timerId: number;
}

export interface SensorGroupDef {
  id: string;
  title: string;
  icon: string;
  order: number;
  default_collapsed: boolean;
  color: string;
}
