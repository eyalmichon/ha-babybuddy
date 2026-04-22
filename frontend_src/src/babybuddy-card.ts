import { LitElement, html, css, nothing, type CSSResultGroup } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type {
  HomeAssistant,
  BabyBuddyCardConfig,
  EntityRegistryEntry,
  ChildEntities,
  BbActionDetail,
  BbTimerStopDetail,
  SensorGroupDef,
} from "./types";
import {
  getVersion,
  childAge,
  discoverChildEntities,
} from "./utils";

import "./components/child-header";
import "./components/timer-bar";
import "./components/activity-chips";
import "./components/action-buttons";
import "./components/action-dialog";

@customElement("babybuddy-card")
export class BabyBuddyCard extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @state() private _config!: BabyBuddyCardConfig;
  @state() private _entityRegistry: EntityRegistryEntry[] = [];
  @state() private _registryLoaded = false;
  @state() private _activeDialog: string | null = null;
  @state() private _dialogTimerId?: number;
  @state() private _activeTab = 0;
  @state() private _sensorGroups: SensorGroupDef[] = [];

  private _cardConfigLoaded = false;
  private _cardConfigLoading = false;
  private _cardConfigAttempts = 0;
  private static readonly _MAX_CONFIG_ATTEMPTS = 10;
  private _unsubRegistry?: (() => void) | undefined;

  public setConfig(config: BabyBuddyCardConfig): void {
    this._config = {
      show_timer: true,
      show_actions: true,
      compact: false,
      ...config,
    };
  }

  public getCardSize(): number {
    return this._config?.compact ? 3 : 5;
  }

  public getGridOptions() {
    return {
      rows: this._config?.compact ? 3 : 5,
      columns: 12,
      min_rows: 3,
      min_columns: 6,
    };
  }

  static getConfigForm() {
    const labels: Record<string, string> = {
      entity: "Child entity (leave empty for all children)",
      show_timer: "Show timer",
      show_actions: "Show action buttons",
      compact: "Compact mode",
    };
    return {
      schema: [
        {
          name: "entity",
          selector: { entity: { integration: "babybuddy" } },
        },
        {
          type: "expandable",
          name: "",
          title: "Display Options",
          flatten: true,
          schema: [
            { name: "show_timer", selector: { boolean: {} } },
            { name: "show_actions", selector: { boolean: {} } },
            { name: "compact", selector: { boolean: {} } },
          ],
        },
      ],
      computeLabel: (schema: { name: string }) =>
        labels[schema.name] ?? schema.name,
    };
  }

  static getStubConfig() {
    return {};
  }

  connectedCallback(): void {
    super.connectedCallback();
    this._loadEntityRegistry();
    this._loadCardConfig();
    this._subscribeRegistryUpdates();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this._unsubRegistry?.();
    this._unsubRegistry = undefined;
  }

  private async _subscribeRegistryUpdates(): Promise<void> {
    if (this._unsubRegistry) return;
    try {
      this._unsubRegistry = await this.hass.connection.subscribeEvents(
        (event: { data?: { action?: string } }) => {
          const action = event.data?.action;
          if (action === "create" || action === "remove") {
            this._loadEntityRegistry();
          }
        },
        "entity_registry_updated",
      );
    } catch {
      // Subscription not available
    }
  }

  private _registryLoading = false;

  private async _loadEntityRegistry(): Promise<void> {
    if (this._registryLoading) return;
    this._registryLoading = true;

    try {
      const list = (await this.hass.callWS({
        type: "config/entity_registry/list",
      })) as EntityRegistryEntry[];

      // The list endpoint doesn't include original_icon.
      // Batch-fetch extended data for BB entities to get their icons.
      // Wrapped separately so a failure here doesn't discard the list.
      const bbIds = list
        .filter((e) => e.platform === "babybuddy")
        .map((e) => e.entity_id);

      if (bbIds.length > 0) {
        try {
          const extended = (await this.hass.callWS({
            type: "config/entity_registry/get_entries",
            entity_ids: bbIds,
          })) as Record<string, { original_icon?: string | null } | null>;

          for (const entry of list) {
            const ext = extended[entry.entity_id];
            if (ext?.original_icon) {
              entry.original_icon = ext.original_icon;
            }
          }
        } catch {
          // Icon enrichment is cosmetic; the card works without it.
        }
      }

      this._entityRegistry = list;
      this._registryLoaded = true;
    } catch {
      // Will retry on next hass update
    } finally {
      this._registryLoading = false;
    }
  }

  private async _loadCardConfig(): Promise<void> {
    if (this._cardConfigLoaded || this._cardConfigLoading) return;
    this._cardConfigLoading = true;
    try {
      const result = (await this.hass.callWS({
        type: "babybuddy/card_config",
      })) as {
        version: string;
        sensor_groups: SensorGroupDef[];
        ready?: boolean;
      };

      this._sensorGroups = result.sensor_groups ?? [];

      // Backward compatible: if backend sends `ready`, use it;
      // otherwise fall back to "non-empty groups" heuristic.
      const isReady = result.ready ?? this._sensorGroups.length > 0;
      if (isReady) this._cardConfigLoaded = true;

      const cardVersion = getVersion();
      if (result.version !== cardVersion) {
        this.dispatchEvent(
          new CustomEvent("hass-notification", {
            detail: {
              message: `Baby Buddy card version mismatch: backend ${result.version}, card ${cardVersion}. Please reload.`,
              duration: -1,
              dismissable: true,
              action: {
                text: "Reload",
                action: () => {
                  const reload = () => globalThis.location.reload();
                  if (typeof caches !== "undefined") {
                    caches
                      .keys()
                      .then((names) =>
                        Promise.all(names.map((n) => caches.delete(n))),
                      )
                      .then(reload, reload);
                  } else {
                    reload();
                  }
                },
              },
            },
            bubbles: true,
            composed: true,
          }),
        );
      }
    } catch {
      // card_config endpoint not available
    } finally {
      this._cardConfigLoading = false;
      this._cardConfigAttempts++;
      if (this._cardConfigAttempts >= BabyBuddyCard._MAX_CONFIG_ATTEMPTS) {
        this._cardConfigLoaded = true;
      }
    }
  }

  private _findChildEntityIds(): string[] {
    if (this._config?.entity) return [this._config.entity];
    if (!this._registryLoaded) return [];

    return this._entityRegistry
      .filter(
        (e) =>
          e.platform === "babybuddy" &&
          e.entity_id.startsWith("sensor.") &&
          e.original_name === null &&
          this.hass.states[e.entity_id]?.state !== "unavailable",
      )
      .map((e) => e.entity_id);
  }

  private _getChildEntities(entityId: string): ChildEntities | null {
    if (!this.hass || !this._registryLoaded) return null;
    return discoverChildEntities(entityId, this.hass, this._entityRegistry);
  }

  private _handleAction(e: CustomEvent<BbActionDetail>): void {
    this._activeDialog = e.detail.action;
    this._dialogTimerId = undefined;
  }

  private _handleTimerStop(e: CustomEvent<BbTimerStopDetail>): void {
    this._activeDialog = e.detail.action;
    this._dialogTimerId = e.detail.timerId;
  }

  private _handleDialogClose(): void {
    this._activeDialog = null;
    this._dialogTimerId = undefined;
  }

  protected updated(changedProps: Map<string, unknown>): void {
    super.updated(changedProps);
    if (changedProps.has("hass") && this.hass) {
      if (!this._registryLoaded) this._loadEntityRegistry();
      if (!this._cardConfigLoaded) this._loadCardConfig();
    }
  }

  protected render() {
    if (!this._config || !this.hass) return nothing;

    if (!this._registryLoaded) {
      return html`
        <ha-card>
          <div class="loading">Loading...</div>
        </ha-card>
      `;
    }

    const childIds = this._findChildEntityIds();

    if (childIds.length === 0) {
      return html`
        <ha-card>
          <div class="not-found">
            No Baby Buddy children found. Make sure the integration is
            configured.
          </div>
        </ha-card>
      `;
    }

    const tabIndex = Math.min(this._activeTab, childIds.length - 1);
    const showTabs = childIds.length > 1;

    const compact = this._config.compact ?? false;

    return html`
      <ha-card class=${compact ? "compact" : ""}>
        ${showTabs ? this._renderTabs(childIds, tabIndex) : nothing}
        ${this._renderChild(childIds[tabIndex])}
      </ha-card>
    `;
  }

  private _renderTabs(childIds: string[], activeIndex: number) {
    return html`
      <div class="tabs" role="tablist">
        ${childIds.map((eid, i) => {
          const entity = this.hass.states[eid];
          const name =
            (entity?.attributes.friendly_name as string) ?? eid;
          const isActive = i === activeIndex;
          return html`
            <button
              class="tab ${isActive ? "active" : ""}"
              role="tab"
              aria-selected=${isActive}
              @click=${() => {
                this._activeTab = i;
                this._activeDialog = null;
                this._dialogTimerId = undefined;
              }}
            >
              ${name}
            </button>
          `;
        })}
      </div>
    `;
  }

  private _renderChild(entityId: string) {
    const child = this._getChildEntities(entityId);
    if (!child?.primary) {
      return html`
        <div class="not-found">
          Entity ${entityId} not found or not loaded yet.
        </div>
      `;
    }

    const primary = child.primary;
    const birthDate =
      (primary.attributes.birth_date as string | undefined) ?? primary.state;
    const name =
      (primary.attributes.friendly_name as string) ?? primary.entity_id;
    const picture = primary.attributes.entity_picture as
      | string
      | undefined;

    return html`
      <bb-child-header
        .name=${name}
        .age=${childAge(birthDate)}
        .picture=${picture}
        .compact=${this._config.compact ?? false}
      ></bb-child-header>

      ${this._config.show_timer
        ? html`
            <bb-timer-bar
              .hass=${this.hass}
              .timers=${child.timers}
              .startTimerButton=${child.startTimerButton}
              .childEntityId=${entityId}
              @bb-timer-stop=${this._handleTimerStop}
            ></bb-timer-bar>
          `
        : nothing}

      ${this._config.show_actions
        ? html`
            <bb-action-buttons
              .hass=${this.hass}
              .childEntity=${primary}
              .entityRegistry=${this._entityRegistry}
              .compact=${this._config.compact ?? false}
              @bb-action=${this._handleAction}
            ></bb-action-buttons>
          `
        : nothing}

      <bb-activity-chips
        .hass=${this.hass}
        .sensors=${child.sensors}
        .binarySensors=${child.binarySensors}
        .entityRegistry=${this._entityRegistry}
        .childPrefix=${primary.entity_id.split(".")[1] ?? ""}
        .sensorGroups=${this._sensorGroups}
        .compact=${this._config.compact ?? false}
      ></bb-activity-chips>
      ${this._activeDialog
        ? html`
            <bb-action-dialog
              .hass=${this.hass}
              .action=${this._activeDialog}
              .childEntity=${primary}
              .timers=${child.timers}
              .selects=${child.selects}
              .initialTimerId=${this._dialogTimerId}
              @bb-dialog-close=${this._handleDialogClose}
            ></bb-action-dialog>
          `
        : nothing}
    `;
  }

  static get styles(): CSSResultGroup {
    return css`
      :host {
        display: block;
      }
      ha-card {
        padding: 16px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }
      ha-card.compact {
        padding: 10px;
        gap: 8px;
      }
      .not-found {
        padding: 16px;
        text-align: center;
        color: var(--secondary-text-color);
        font-size: 0.9rem;
      }
      .loading {
        padding: 24px 16px;
        text-align: center;
        color: var(--secondary-text-color);
        font-size: 0.9rem;
      }
      .loading::after {
        content: "";
        display: block;
        width: 24px;
        height: 24px;
        margin: 12px auto 0;
        border: 2px solid var(--divider-color);
        border-top-color: var(--primary-color);
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
      }
      .tabs {
        display: flex;
        gap: 4px;
        margin-bottom: 12px;
        border-bottom: 1px solid var(--divider-color);
        padding-bottom: 8px;
        overflow-x: auto;
        scrollbar-width: none;
      }
      .tabs::-webkit-scrollbar {
        display: none;
      }
      .tab {
        padding: 6px 14px;
        border: none;
        border-radius: 16px;
        background: none;
        color: var(--secondary-text-color);
        cursor: pointer;
        font-size: 0.85rem;
        font-family: inherit;
        font-weight: 500;
        white-space: nowrap;
        transition: all 0.2s ease;
        outline: none;
      }
      .tab.active {
        background: var(--primary-color);
        color: var(--text-primary-color);
      }
      @media (hover: hover) {
        .tab:not(.active):hover {
          background: var(--secondary-background-color);
        }
      }
      .tab:not(.active):focus-visible {
        background: var(--secondary-background-color);
      }
      .tab:focus-visible {
        box-shadow: 0 0 0 2px var(--primary-color);
      }
      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }
    `;
  }
}

window.customCards = window.customCards || [];
window.customCards.push({
  type: "babybuddy-card",
  name: "Baby Buddy",
  preview: true,
  description: "Track feedings, sleep, diapers, and more",
  documentationURL: "https://github.com/eyalmichon/ha-babybuddy",
});

declare global {
  interface Window {
    customCards: Array<{
      type: string;
      name: string;
      preview?: boolean;
      description?: string;
      documentationURL?: string;
    }>;
  }
}
