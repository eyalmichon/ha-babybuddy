import { LitElement, html, css, nothing, type CSSResultGroup } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type {
  HomeAssistant,
  HassEntity,
  EntityRegistryEntry,
  BbActionDetail,
} from "../types";
import {
  buildKeywordIconMap,
  labelForServiceKey,
  resolveServiceIcon,
} from "../utils";

interface ActionDef {
  key: string;
  label: string;
  icon: string;
}

/** Services that should not appear as action buttons. */
const HIDDEN_SERVICES = new Set([
  "delete_last_entry",
  "add_child",
  "start_timer",
  "stop_timer",
]);

/** Priority order — services whose key contains these substrings sort first. */
const PRIORITY: string[] = [
  "feeding",
  "diaper",
  "change",
  "sleep",
  "tummy",
  "pumping",
  "medication",
];

function sortOrder(key: string): number {
  for (const [i, pattern] of PRIORITY.entries()) {
    if (key.includes(pattern)) return i;
  }
  return 100;
}

@customElement("bb-action-buttons")
export class ActionButtons extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property({ attribute: false }) public childEntity!: HassEntity;
  @property({ attribute: false }) public entityRegistry: EntityRegistryEntry[] = [];
  @property({ type: Boolean }) public compact = false;
  @state() private _showMore = false;

  private _getAvailableActions(): ActionDef[] {
    const services = this.hass?.services?.babybuddy;
    if (!services) return [];

    const iconMap = buildKeywordIconMap(this.entityRegistry);

    return Object.keys(services)
      .filter((k) => !HIDDEN_SERVICES.has(k) && !k.startsWith("_"))
      .map((key) => ({
        key,
        label: (services[key] as { name?: string }).name ?? labelForServiceKey(key),
        icon: resolveServiceIcon(key, iconMap),
      }))
      .sort((a, b) => sortOrder(a.key) - sortOrder(b.key));
  }

  private _fireAction(key: string): void {
    this.dispatchEvent(
      new CustomEvent<BbActionDetail>("bb-action", {
        detail: { action: key },
        bubbles: true,
        composed: true,
      }),
    );
  }

  protected render() {
    const actions = this._getAvailableActions();
    const visible = this._showMore ? actions : actions.slice(0, 4);

    return html`
      <div class="actions ${this.compact ? "compact" : ""}">
        ${visible.map(
          (a) => html`
            <button
              class="action-btn"
              title=${a.label}
              @click=${() => this._fireAction(a.key)}
            >
              <ha-icon icon=${a.icon}></ha-icon>
              ${this.compact ? nothing : html`<span>${a.label}</span>`}
            </button>
          `,
        )}
        ${actions.length > 4 && !this._showMore
          ? html`
              <button
                class="action-btn more"
                title="More actions"
                @click=${() => (this._showMore = true)}
              >
                <ha-icon icon="mdi:dots-horizontal"></ha-icon>
                ${this.compact ? nothing : html`<span>More</span>`}
              </button>
            `
          : actions.length > 4 && this._showMore
            ? html`
                <button
                  class="action-btn more"
                  title="Show less"
                  @click=${() => (this._showMore = false)}
                >
                  <ha-icon icon="mdi:chevron-up"></ha-icon>
                  ${this.compact ? nothing : html`<span>Less</span>`}
                </button>
              `
            : nothing}
      </div>
    `;
  }

  static get styles(): CSSResultGroup {
    return css`
      :host {
        display: block;
      }
      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }
      .action-btn {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 6px 12px;
        border: 1px solid var(--divider-color);
        border-radius: 18px;
        background: none;
        color: var(--primary-text-color);
        cursor: pointer;
        font-size: 0.8rem;
        font-family: inherit;
        transition: all 0.2s ease;
        --mdc-icon-size: 18px;
        outline: none;
      }
      .action-btn:hover,
      .action-btn:focus-visible {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border-color: var(--primary-color);
      }
      .action-btn:focus-visible {
        box-shadow: 0 0 0 2px var(--primary-color);
      }
      .action-btn:active {
        transform: scale(0.96);
      }
      .action-btn.more {
        border-style: dashed;
      }
      .actions.compact {
        gap: 4px;
      }
      .actions.compact .action-btn {
        padding: 6px;
        border-radius: 50%;
        --mdc-icon-size: 16px;
      }
    `;
  }
}
