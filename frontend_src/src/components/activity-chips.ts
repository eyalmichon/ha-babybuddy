import { LitElement, html, css, nothing, type CSSResultGroup } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type {
  HomeAssistant,
  HassEntity,
  EntityRegistryEntry,
  SensorGroupDef,
} from "../types";
import {
  timeSince,
  formatDuration,
  extractActivityKey,
  labelForServiceKey,
  resolveIcon,
} from "../utils";

interface RowData {
  icon: string;
  label: string;
  value: string;
  color: string;
  entityId: string;
}

interface SensorGroup {
  id: string;
  title: string;
  icon: string;
  color: string;
  rows: RowData[];
  collapsed: boolean;
}

const OTHER_GROUP_ID = "__other__";

const _HA_INTERNAL_KEYS = new Set([
  "device_class",
  "state_class",
  "unit_of_measurement",
  "friendly_name",
  "icon",
  "bb_group",
  "bb_color",
  "entity_picture",
  "supported_features",
  "attribution",
  "timer_id",
  "timer_name",
]);

@customElement("bb-activity-chips")
export class ActivityChips extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property({ attribute: false }) public sensors: HassEntity[] = [];
  @property({ attribute: false }) public binarySensors: HassEntity[] = [];
  @property({ attribute: false })
  public entityRegistry: EntityRegistryEntry[] = [];
  @property() public childPrefix = "";
  @property({ attribute: false }) public sensorGroups: SensorGroupDef[] = [];
  @property({ type: Boolean }) public compact = false;

  private static readonly _STORAGE_KEY_PREFIX = "bb-card-collapsed";

  @state() private _collapsed: Record<string, boolean> = {};
  @state() private _expandedRows = new Set<string>();
  @state() private _pendingDelete: string | null = null;
  @state() private _deleteError: string | null = null;
  private _defaultsApplied = false;
  private _deleteErrorTimeout?: ReturnType<typeof setTimeout>;
  private _prevChildPrefix = "";
  private _cachedGroups: SensorGroup[] = [];
  private _groupsDirty = true;

  private get _storageKey(): string {
    return this.childPrefix
      ? `${ActivityChips._STORAGE_KEY_PREFIX}-${this.childPrefix}`
      : ActivityChips._STORAGE_KEY_PREFIX;
  }

  protected willUpdate(changedProperties: Map<string, unknown>): void {
    if (changedProperties.has("childPrefix") && this.childPrefix !== this._prevChildPrefix) {
      this._prevChildPrefix = this.childPrefix;
      this._defaultsApplied = false;
    }

    if (!this._defaultsApplied) {
      this._applyDefaults();
    }

    if (
      changedProperties.has("sensors") ||
      changedProperties.has("binarySensors") ||
      changedProperties.has("sensorGroups") ||
      changedProperties.has("_collapsed")
    ) {
      this._groupsDirty = true;
    }
  }

  private _buildRow(entity: HassEntity): RowData {
    const key = extractActivityKey(entity.entity_id, this.childPrefix);
    const icon = resolveIcon(
      entity.entity_id,
      this.entityRegistry,
      "mdi:clock-outline",
    );
    const label = labelForServiceKey(key);
    const dc = entity.attributes.device_class as string | undefined;
    let value: string;
    if (dc === "timestamp") {
      value = timeSince(entity.state);
    } else if (dc === "duration" && !isNaN(Number(entity.state))) {
      value = formatDuration(Math.round(Number(entity.state)));
    } else {
      value = this.hass.formatEntityState(entity);
    }

    const color = (entity.attributes.bb_color as string) ?? "";
    return { icon, label, value, color, entityId: entity.entity_id };
  }

  private _applyDefaults(): void {
    if (this._defaultsApplied) return;
    try {
      const saved = localStorage.getItem(this._storageKey);
      if (saved) {
        this._collapsed = JSON.parse(saved);
        this._defaultsApplied = true;
        return;
      }
    } catch {
      // localStorage unavailable or corrupt -- fall through to defaults
    }
    const c: Record<string, boolean> = {};
    for (const def of this.sensorGroups) {
      c[def.id] = def.default_collapsed;
    }
    c[OTHER_GROUP_ID] = true;
    this._collapsed = c;
    this._defaultsApplied = true;
  }

  private _buildGroups(): SensorGroup[] {
    if (!this._groupsDirty) return this._cachedGroups;
    this._groupsDirty = false;

    const groupMap = new Map<string, SensorGroupDef>();
    for (const def of this.sensorGroups) {
      groupMap.set(def.id, def);
    }

    const buckets: Record<string, RowData[]> = {};
    for (const def of this.sensorGroups) buckets[def.id] = [];
    buckets[OTHER_GROUP_ID] = [];

    for (const entity of this.sensors) {
      if (
        !entity.state ||
        entity.state === "unknown" ||
        entity.state === "unavailable"
      )
        continue;

      const groupId =
        (entity.attributes.bb_group as string | undefined) ?? "";
      if (groupId && buckets[groupId]) {
        buckets[groupId].push(this._buildRow(entity));
      } else {
        buckets[OTHER_GROUP_ID].push(this._buildRow(entity));
      }
    }

    for (const entity of this.binarySensors) {
      if (entity.state === "unavailable") continue;
      const key = extractActivityKey(entity.entity_id, this.childPrefix);
      const icon = resolveIcon(
        entity.entity_id,
        this.entityRegistry,
        entity.state === "on" ? "mdi:check-circle" : "mdi:circle-outline",
      );
      const label = labelForServiceKey(key);
      const value = entity.state === "on" ? "Yes" : "No";
      const bsColor = (entity.attributes.bb_color as string) ?? "";
      const groupId =
        (entity.attributes.bb_group as string | undefined) ?? "";
      const target =
        groupId && buckets[groupId] ? groupId : OTHER_GROUP_ID;
      buckets[target].push({
        icon,
        label,
        value,
        color: bsColor,
        entityId: entity.entity_id,
      });
    }

    const sorted = [...this.sensorGroups].sort((a, b) => a.order - b.order);
    const result: SensorGroup[] = [];

    for (const def of sorted) {
      if (buckets[def.id].length > 0) {
        result.push({
          id: def.id,
          title: def.title,
          icon: def.icon,
          color: def.color ?? "",
          rows: buckets[def.id],
          collapsed: this._collapsed[def.id] ?? def.default_collapsed,
        });
      }
    }

    if (buckets[OTHER_GROUP_ID].length > 0) {
      result.push({
        id: OTHER_GROUP_ID,
        title: "Other",
        icon: "mdi:information-outline",
        color: "",
        rows: buckets[OTHER_GROUP_ID],
        collapsed: this._collapsed[OTHER_GROUP_ID] ?? true,
      });
    }

    this._cachedGroups = result;
    return result;
  }

  private _toggleGroup(id: string): void {
    this._collapsed = {
      ...this._collapsed,
      [id]: !this._collapsed[id],
    };
    try {
      localStorage.setItem(
        this._storageKey,
        JSON.stringify(this._collapsed),
      );
    } catch {
      // localStorage unavailable -- state still works in-memory
    }
  }

  private _toggleRow(entityId: string): void {
    const next = new Set(this._expandedRows);
    if (next.has(entityId)) next.delete(entityId);
    else next.add(entityId);
    this._expandedRows = next;
  }

  private _bbAttributes(entityId: string): [string, unknown][] {
    const entity = this.hass.states[entityId];
    if (!entity) return [];
    return Object.entries(entity.attributes).filter(
      ([k, v]) => !_HA_INTERNAL_KEYS.has(k) && v != null && v !== "",
    );
  }

  private static _formatKey(key: string): string {
    return key
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }

  private get _canDelete(): boolean {
    return !!this.hass.services?.babybuddy?.delete_last_entry;
  }

  private _hasEntryId(entityId: string): boolean {
    const entity = this.hass.states[entityId];
    return entity?.attributes?.id != null;
  }

  private _confirmDelete(entityId: string): void {
    this._pendingDelete = entityId;
  }

  private _cancelDelete(): void {
    this._pendingDelete = null;
  }

  private async _executeDelete(entityId: string): Promise<void> {
    this._pendingDelete = null;
    try {
      await this.hass.callService("babybuddy", "delete_last_entry", {
        entity_id: entityId,
      });
    } catch (err: unknown) {
      this._deleteError =
        err instanceof Error ? err.message : "Failed to delete entry";
      if (this._deleteErrorTimeout) clearTimeout(this._deleteErrorTimeout);
      this._deleteErrorTimeout = setTimeout(() => {
        this._deleteError = null;
      }, 5000);
    }
  }

  protected render() {
    const groups = this._buildGroups();
    if (groups.length === 0) return nothing;

    return html`
      <div class="sections ${this.compact ? "compact" : ""}">
        ${groups.map((g) => this._renderGroup(g))}
      </div>
    `;
  }

  private _renderGroup(group: SensorGroup) {
    return html`
      <div class="group">
        <button
          class="group-header"
          @click=${() => this._toggleGroup(group.id)}
        >
          <ha-icon icon=${group.icon} class="group-icon"></ha-icon>
          <span class="group-title">${group.title}</span>
          <span class="group-count">${group.rows.length}</span>
          <ha-icon
            icon=${group.collapsed ? "mdi:chevron-down" : "mdi:chevron-up"}
            class="group-toggle"
          ></ha-icon>
        </button>
        ${group.collapsed
          ? nothing
          : html`
              <div class="group-body">
                ${group.rows.map((r) => this._renderRow(r))}
              </div>
            `}
      </div>
    `;
  }

  private _renderRow(r: RowData) {
    const expanded = this._expandedRows.has(r.entityId);
    const details = expanded ? this._bbAttributes(r.entityId) : [];
    return html`
      <div class="row-block">
        ${this._renderRowHeader(r, expanded)}
        ${expanded && details.length > 0
          ? this._renderRowDetail(details)
          : nothing}
        ${expanded && this._canDelete && this._hasEntryId(r.entityId)
          ? this._renderDeleteAction(r.entityId)
          : nothing}
      </div>
    `;
  }

  private _renderRowHeader(r: RowData, expanded: boolean) {
    return html`
      <div
        class="row ${expanded ? "expanded" : ""}"
        role="button"
        tabindex="0"
        aria-expanded=${expanded}
        @click=${() => this._toggleRow(r.entityId)}
        @keydown=${(e: KeyboardEvent) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            this._toggleRow(r.entityId);
          }
        }}
      >
        <ha-icon
          icon=${r.icon}
          class="row-icon"
          style=${r.color ? `color: ${r.color}` : ""}
        ></ha-icon>
        <span class="row-label">${r.label}</span>
        <span class="row-value">${r.value}</span>
        <ha-icon
          icon=${expanded ? "mdi:chevron-up" : "mdi:chevron-down"}
          class="row-toggle"
        ></ha-icon>
      </div>
    `;
  }

  private _renderRowDetail(details: [string, unknown][]) {
    return html`
      <div class="row-detail">
        ${details.map(
          ([k, v]) => html`
            <div class="detail-item">
              <span class="detail-key">${ActivityChips._formatKey(k)}</span>
              <span class="detail-val">${v}</span>
            </div>
          `,
        )}
      </div>
    `;
  }

  private _renderDeleteAction(entityId: string) {
    const confirming = this._pendingDelete === entityId;
    return html`
      <div class="row-actions">
        <button
          class="delete-btn ${confirming ? "confirming" : ""}"
          @click=${(e: Event) => {
            e.stopPropagation();
            if (!confirming) this._confirmDelete(entityId);
          }}
        >
          <span class="delete-default">
            <ha-icon icon="mdi:delete-outline"></ha-icon>
            Delete
          </span>
          <span class="delete-confirm">
            <span class="confirm-label">Delete?</span>
            <span
              class="confirm-yes"
              @click=${(e: Event) => {
                e.stopPropagation();
                this._executeDelete(entityId);
              }}
            >Yes</span>
            <span
              class="confirm-cancel"
              @click=${(e: Event) => {
                e.stopPropagation();
                this._cancelDelete();
              }}
            >Cancel</span>
          </span>
        </button>
        ${this._deleteError && this._pendingDelete === null
          ? html`<div class="delete-error">${this._deleteError}</div>`
          : nothing}
      </div>
    `;
  }

  static get styles(): CSSResultGroup {
    return css`
      :host {
        display: block;
      }
      .sections {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }

      /* ── Group chrome ── */
      .group {
        border-radius: 12px;
        overflow: hidden;
        background: var(--secondary-background-color);
      }
      .group-header {
        display: flex;
        align-items: center;
        gap: 8px;
        width: 100%;
        padding: 8px 12px;
        border: none;
        background: none;
        color: var(--primary-text-color);
        cursor: pointer;
        font-family: inherit;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        outline: none;
        --mdc-icon-size: 16px;
      }
      @media (hover: hover) {
        .group-header:hover {
          background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.08);
        }
      }
      .group-header:focus-visible {
        box-shadow: inset 0 0 0 2px var(--primary-color);
      }
      .group-icon {
        color: var(--secondary-text-color);
        flex-shrink: 0;
      }
      .group-title {
        flex: 1;
        text-align: left;
      }
      .group-count {
        color: var(--secondary-text-color);
        font-size: 0.72rem;
        font-weight: 400;
        background: var(--card-background-color, var(--ha-card-background));
        padding: 1px 7px;
        border-radius: 10px;
      }
      .group-toggle {
        color: var(--secondary-text-color);
        flex-shrink: 0;
        transition: transform 0.2s ease;
      }
      .group-body {
        padding: 0 4px 4px;
      }

      /* ── Row header ── */
      .row {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 8px;
        border-radius: 8px;
        font-size: 0.85rem;
        transition: background 0.15s ease;
        --mdc-icon-size: 18px;
      }
      @media (hover: hover) {
        .row:hover {
          background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.05);
        }
      }
      .row-icon {
        flex-shrink: 0;
        color: var(--secondary-text-color);
      }
      .row-label {
        flex: 1;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        color: var(--primary-text-color);
      }
      .row-value {
        flex-shrink: 0;
        font-weight: 500;
        color: var(--secondary-text-color);
        font-variant-numeric: tabular-nums;
        text-align: right;
      }
      .row-toggle {
        flex-shrink: 0;
        color: var(--disabled-text-color, #999);
        --mdc-icon-size: 14px;
      }
      .row.expanded {
        background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.06);
      }

      /* ── Expanded detail key/value pairs ── */
      .row-detail {
        padding: 2px 8px 6px 44px;
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .detail-item {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        font-size: 0.78rem;
        line-height: 1.4;
      }
      .detail-key {
        color: var(--secondary-text-color);
        white-space: nowrap;
      }
      .detail-val {
        color: var(--primary-text-color);
        text-align: right;
        word-break: break-word;
        min-width: 0;
      }

      /* ── Delete action (lives outside .row-detail, centered) ── */
      .row-actions {
        padding: 0 8px 4px;
      }
      .delete-btn {
        position: relative;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        margin-top: 4px;
        padding: 6px 8px;
        border: none;
        border-radius: 6px;
        background: rgba(var(--rgb-error-color, 219, 68, 55), 0.1);
        color: var(--error-color, #db4437);
        font-family: inherit;
        font-size: 0.75rem;
        cursor: pointer;
        --mdc-icon-size: 14px;
      }
      @media (hover: hover) {
        .delete-btn:hover {
          background: rgba(var(--rgb-error-color, 219, 68, 55), 0.18);
        }
      }
      .delete-btn:focus-visible {
        box-shadow: 0 0 0 2px var(--error-color, #db4437);
        outline: none;
      }
      .delete-btn.confirming {
        background: rgba(var(--rgb-error-color, 219, 68, 55), 0.15);
        cursor: default;
      }
      @media (hover: hover) {
        .delete-btn.confirming:hover {
          background: rgba(var(--rgb-error-color, 219, 68, 55), 0.15);
        }
      }

      .delete-default {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
      }
      .delete-btn.confirming .delete-default {
        visibility: hidden;
      }

      .delete-confirm {
        position: absolute;
        inset: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        opacity: 0;
        pointer-events: none;
      }
      .delete-btn.confirming .delete-confirm {
        opacity: 1;
        pointer-events: auto;
      }

      .confirm-yes,
      .confirm-cancel {
        min-width: 48px;
        padding: 2px 10px;
        border-radius: 4px;
        cursor: pointer;
        font-weight: 600;
        font-size: 0.75rem;
        text-align: center;
      }
      .confirm-yes {
        background: var(--error-color, #db4437);
        color: #fff;
      }
      @media (hover: hover) {
        .confirm-yes:hover {
          opacity: 0.85;
        }
      }
      .confirm-cancel {
        background: var(--card-background-color, var(--ha-card-background));
        color: var(--primary-text-color);
      }
      @media (hover: hover) {
        .confirm-cancel:hover {
          opacity: 0.8;
        }
      }

      .delete-error {
        margin-top: 4px;
        padding: 4px 8px;
        font-size: 0.75rem;
        color: var(--error-color, #db4437);
      }

      /* ── Compact overrides ── */
      .sections.compact .group-header {
        padding: 6px 10px;
        font-size: 0.72rem;
        --mdc-icon-size: 14px;
      }
      .sections.compact .row {
        padding: 4px 8px;
        font-size: 0.78rem;
        --mdc-icon-size: 16px;
      }
    `;
  }
}
