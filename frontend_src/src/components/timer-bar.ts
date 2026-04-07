import { LitElement, html, css, nothing, type CSSResultGroup } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, HassEntity, BbTimerStopDetail } from "../types";
import { labelForServiceKey } from "../utils";

interface TimerAction {
  key: string;
  label: string;
}

@customElement("bb-timer-bar")
export class TimerBar extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property({ attribute: false }) public timers: HassEntity[] = [];
  @property({ attribute: false })
  public startTimerButton: HassEntity | null = null;
  @property({ attribute: false }) public childEntityId = "";

  @state() private _elapsed: Record<string, string> = {};
  @state() private _expandedTimerId: string | null = null;
  @state() private _error: string | null = null;
  @state() private _busy = false;
  @state() private _pendingStart: string | null = null;
  @state() private _hiddenTimerIds = new Set<string>();
  @state() private _startExpanded = false;
  @state() private _editingTimerEntityId: string | null = null;
  @state() private _editingName = "";
  private _interval?: ReturnType<typeof setInterval>;
  private _boundDocClick?: (e: Event) => void;
  private _boundKeyDown?: (e: KeyboardEvent) => void;
  private _errorTimeout?: ReturnType<typeof setTimeout>;

  connectedCallback(): void {
    super.connectedCallback();
    this._syncInterval();
    this._boundDocClick = (e: Event) => {
      const path = e.composedPath();
      const isInside = path.includes(this);
      if (!isInside) {
        if (this._expandedTimerId) this._expandedTimerId = null;
        if (this._startExpanded) this._startExpanded = false;
      }
    };
    document.addEventListener("click", this._boundDocClick);

    this._boundKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (this._expandedTimerId) this._expandedTimerId = null;
        if (this._startExpanded) this._startExpanded = false;
      }
    };
    document.addEventListener("keydown", this._boundKeyDown);
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    if (this._interval) {
      clearInterval(this._interval);
      this._interval = undefined;
    }
    if (this._errorTimeout) clearTimeout(this._errorTimeout);
    if (this._boundDocClick) {
      document.removeEventListener("click", this._boundDocClick);
    }
    if (this._boundKeyDown) {
      document.removeEventListener("keydown", this._boundKeyDown);
    }
  }

  protected willUpdate(changedProperties: Map<string, unknown>): void {
    if (changedProperties.has("timers")) {
      this._syncInterval();
      if (this._pendingStart) this._pendingStart = null;
      const currentIds = new Set(this.timers.map((t) => t.entity_id));
      for (const id of this._hiddenTimerIds) {
        if (!currentIds.has(id)) this._hiddenTimerIds.delete(id);
      }
      if (this._hiddenTimerIds.size > 0) {
        this._hiddenTimerIds = new Set(this._hiddenTimerIds);
      }
    }
  }

  private _syncInterval(): void {
    const visibleTimers = this.timers.filter(
      (t) => !this._hiddenTimerIds.has(t.entity_id),
    );
    if (visibleTimers.length > 0 || this._pendingStart) {
      if (!this._interval) {
        this._tick();
        this._interval = setInterval(() => this._tick(), 1000);
      }
    } else if (this._interval) {
      clearInterval(this._interval);
      this._interval = undefined;
    }
  }

  private _tick(): void {
    const next: Record<string, string> = {};
    for (const entity of this.timers) {
      const start = entity.state;
      if (!start || start === "unavailable" || start === "unknown") {
        next[entity.entity_id] = "0:00:00";
        continue;
      }
      const diff = Date.now() - new Date(start).getTime();
      if (diff < 0) {
        next[entity.entity_id] = "0:00:00";
        continue;
      }
      const h = Math.floor(diff / 3_600_000);
      const m = Math.floor((diff % 3_600_000) / 60_000);
      const s = Math.floor((diff % 60_000) / 1000);
      next[entity.entity_id] = `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
    }
    this._elapsed = next;
  }

  private _getTimerActions(): TimerAction[] {
    const services = this.hass?.services?.babybuddy;
    if (!services) return [];
    return Object.entries(services)
      .filter(([, svc]) => svc.fields && "timer" in svc.fields)
      .map(([key, svc]) => ({
        key,
        label: labelForServiceKey(key),
      }));
  }

  private _selectAction(action: string, entity: HassEntity): void {
    const timerId = entity.attributes.timer_id as number | undefined;
    if (timerId == null) return;
    this._expandedTimerId = null;
    this.dispatchEvent(
      new CustomEvent<BbTimerStopDetail>("bb-timer-stop", {
        detail: { action, timerId },
        bubbles: true,
        composed: true,
      }),
    );
  }

  private _showError(msg: string): void {
    this._error = msg;
    if (this._errorTimeout) clearTimeout(this._errorTimeout);
    this._errorTimeout = setTimeout(() => {
      this._error = null;
    }, 5000);
  }

  private async _discardTimer(entity: HassEntity): Promise<void> {
    const timerId = entity.attributes.timer_id as number | undefined;
    if (timerId == null) return;
    this._expandedTimerId = null;
    this._hiddenTimerIds.add(entity.entity_id);
    this._hiddenTimerIds = new Set(this._hiddenTimerIds);
    try {
      await this.hass.callService("babybuddy", "stop_timer", {
        timer_id: timerId,
      });
    } catch (err: unknown) {
      this._hiddenTimerIds.delete(entity.entity_id);
      this._hiddenTimerIds = new Set(this._hiddenTimerIds);
      this._showError(
        err instanceof Error ? err.message : "Failed to stop timer",
      );
    }
  }

  private async _startTimer(name?: string): Promise<void> {
    if (!this.childEntityId || this._busy) return;
    this._busy = true;
    this._startExpanded = false;
    const label = name || "Timer";
    try {
      const data: Record<string, unknown> = { child: this.childEntityId };
      if (name) data.name = name;
      await this.hass.callService("babybuddy", "start_timer", data);
      this._pendingStart = label;
    } catch (err: unknown) {
      this._showError(
        err instanceof Error ? err.message : "Failed to start timer",
      );
    } finally {
      this._busy = false;
    }
  }

  private _beginEdit(entity: HassEntity, e: Event): void {
    e.stopPropagation();
    this._editingTimerEntityId = entity.entity_id;
    this._editingName =
      (entity.attributes.timer_name as string) ?? "Timer";
  }

  private async _commitRename(entity: HassEntity): Promise<void> {
    const timerId = entity.attributes.timer_id as number | undefined;
    const name = this._editingName.trim();
    this._editingTimerEntityId = null;
    if (timerId == null || !name) return;
    try {
      await this.hass.callService("babybuddy", "rename_timer", {
        timer_id: timerId,
        name,
      });
    } catch (err: unknown) {
      this._showError(
        err instanceof Error ? err.message : "Failed to rename timer",
      );
    }
  }

  private _cancelEdit(): void {
    this._editingTimerEntityId = null;
  }

  protected render() {
    const visibleTimers = this.timers.filter(
      (t) => !this._hiddenTimerIds.has(t.entity_id),
    );

    return html`
      ${visibleTimers.length > 0
        ? visibleTimers.map((entity) => this._renderTimer(entity))
        : nothing}
      ${this._pendingStart
        ? html`
            <div class="timer active pending">
              <div class="timer-face">
                <ha-icon icon="mdi:timer" class="icon"></ha-icon>
                <span class="label">${this._pendingStart}</span>
                <span class="elapsed">0:00:00</span>
              </div>
            </div>
          `
        : nothing}
      ${this._renderStartArea()}
      ${this._error
        ? html`<div class="error">${this._error}</div>`
        : nothing}
    `;
  }

  private _renderStartArea() {
    if (!this.childEntityId) return nothing;
    const expanded = this._startExpanded;
    const actions = this._getTimerActions();
    return html`
      <div
        class="elastic-shell ${expanded ? "open" : ""}"
        @click=${(e: Event) => e.stopPropagation()}
      >
        <button
          class="elastic-trigger ${expanded ? "shrunk" : ""}"
          ?disabled=${this._busy}
          @click=${(e: Event) => {
            e.stopPropagation();
            if (expanded) {
              this._startExpanded = false;
            } else {
              this._startExpanded = true;
            }
          }}
        >
          <ha-icon icon="mdi:timer-plus"></ha-icon>
          <span>${this._busy ? "Starting..." : "Start Timer"}</span>
        </button>
        <div class="elastic-opts ${expanded ? "open" : ""}">
          ${expanded
            ? html`
                ${actions.map(
                  (a) => html`
                    <button
                      class="elastic-opt"
                      @click=${() => this._startTimer(a.label)}
                    >
                      ${a.label}
                    </button>
                  `,
                )}
                <button
                  class="elastic-opt unnamed"
                  @click=${() => this._startTimer()}
                  title="Start unnamed timer"
                >
                  <ha-icon icon="mdi:timer-outline"></ha-icon>
                </button>
              `
            : nothing}
        </div>
      </div>
    `;
  }

  private _renderTimer(entity: HassEntity) {
    const isExpanded = this._expandedTimerId === entity.entity_id;
    const timerName =
      (entity.attributes.timer_name as string) ??
      (entity.attributes.friendly_name as string) ??
      "Timer";
    const elapsed = this._elapsed[entity.entity_id] ?? "0:00:00";
    const isEditing = this._editingTimerEntityId === entity.entity_id;
    const actions = this._getTimerActions();

    return html`
      <div
        class="timer active"
        @click=${(e: Event) => e.stopPropagation()}
      >
        <div class="timer-face ${isExpanded ? "hidden" : ""}">
          <ha-icon icon="mdi:timer" class="icon"></ha-icon>
          ${isEditing
            ? html`
                <input
                  class="rename-input"
                  .value=${this._editingName}
                  @input=${(e: InputEvent) => {
                    this._editingName = (e.target as HTMLInputElement).value;
                  }}
                  @keydown=${(e: KeyboardEvent) => {
                    if (e.key === "Enter") this._commitRename(entity);
                    if (e.key === "Escape") this._cancelEdit();
                  }}
                  @blur=${() => this._commitRename(entity)}
                  @click=${(e: Event) => e.stopPropagation()}
                />
              `
            : html`
                <span
                  class="label editable"
                  @click=${(e: Event) => this._beginEdit(entity, e)}
                  title="Click to rename"
                >${timerName}</span>
              `}
          <span class="elapsed">${elapsed}</span>
          <button
            class="toggle"
            title="Stop timer"
            @click=${(e: Event) => {
              e.stopPropagation();
              this._editingTimerEntityId = null;
              this._startExpanded = false;
              this._expandedTimerId = entity.entity_id;
            }}
          >
            <ha-icon icon="mdi:stop"></ha-icon>
          </button>
        </div>
        <div class="timer-opts ${isExpanded ? "open" : ""}">
          <button
            class="elastic-opt discard"
            @click=${() => this._discardTimer(entity)}
          >
            <ha-icon icon="mdi:delete-outline"></ha-icon>
          </button>
          ${actions.map(
            (a) => html`
              <button
                class="elastic-opt"
                @click=${() => this._selectAction(a.key, entity)}
              >
                ${a.label}
              </button>
            `,
          )}
        </div>
      </div>
    `;
  }

  protected updated(): void {
    if (this._editingTimerEntityId) {
      const input = this.shadowRoot?.querySelector(
        ".rename-input",
      ) as HTMLInputElement | null;
      if (input && this.shadowRoot?.activeElement !== input) {
        input.focus();
        input.select();
      }
    }
  }

  static get styles(): CSSResultGroup {
    return css`
      :host {
        display: block;
      }
      .timer {
        display: flex;
        align-items: stretch;
        gap: 0;
        padding: 0;
        border-radius: 12px;
        background: var(--card-background-color, var(--ha-card-background));
        border: 1px solid var(--divider-color);
        margin-bottom: 8px;
        overflow: hidden;
        transition: all 0.3s ease;
      }
      .timer.active {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border-color: var(--primary-color);
      }
      .timer.active .icon {
        animation: pulse 1.5s ease-in-out infinite;
      }
      .timer.pending {
        opacity: 0.7;
      }
      .label {
        font-weight: 500;
        font-size: 0.9rem;
        min-width: 0;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .label.editable {
        cursor: pointer;
        border-bottom: 1px dashed rgba(255, 255, 255, 0.4);
      }
      .rename-input {
        font-weight: 500;
        font-size: 0.9rem;
        font-family: inherit;
        background: rgba(255, 255, 255, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.5);
        border-radius: 6px;
        color: inherit;
        padding: 2px 6px;
        min-width: 0;
        width: 120px;
        outline: none;
      }
      .elapsed {
        flex: 1;
        text-align: right;
        font-variant-numeric: tabular-nums;
        font-size: 1.1rem;
        font-weight: 600;
      }
      .toggle {
        background: none;
        border: none;
        cursor: pointer;
        color: inherit;
        padding: 4px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        --mdc-icon-size: 24px;
      }
      .toggle:hover {
        background: rgba(255, 255, 255, 0.2);
      }
      .timer-face {
        display: flex;
        align-items: center;
        gap: 8px;
        flex: 1;
        min-width: 0;
        padding: 8px 12px;
        overflow: hidden;
        transition: flex 0.3s ease, opacity 0.2s ease, padding 0.3s ease;
      }
      .timer-face.hidden {
        flex: 0;
        opacity: 0;
        padding: 8px 0;
        pointer-events: none;
      }
      .timer-opts {
        display: flex;
        align-items: stretch;
        flex: 0;
        overflow: hidden;
        transition: flex 0.3s ease, opacity 0.2s ease;
        opacity: 0;
      }
      .timer-opts.open {
        flex: 1;
        opacity: 1;
      }
      .timer-opts .elastic-opt {
        border-left-color: rgba(255, 255, 255, 0.15);
        color: inherit;
      }
      .timer-opts .elastic-opt:hover {
        background: rgba(255, 255, 255, 0.15);
        color: inherit;
      }
      .elastic-opt.discard {
        flex: 0 0 42px;
        padding: 8px;
        border-left: none;
        --mdc-icon-size: 18px;
      }
      .timer-opts .elastic-opt.discard {
        color: var(--error-color, #db4437);
        background: rgba(0, 0, 0, 0.15);
      }
      .timer-opts .elastic-opt.discard:hover {
        background: var(--error-color, #db4437);
        color: var(--text-primary-color);
      }
      .elastic-shell {
        display: flex;
        gap: 0;
        border-radius: 12px;
        overflow: hidden;
        border: 1px dashed color-mix(in srgb, var(--primary-color) 40%, transparent);
        margin-bottom: 8px;
        transition: all 0.3s ease;
      }
      .elastic-shell.open {
        border-style: solid;
        border-color: var(--primary-color);
      }
      .elastic-trigger {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 8px 10px;
        border: none;
        background: none;
        color: var(--primary-text-color);
        cursor: pointer;
        font-size: 0.85rem;
        font-family: inherit;
        font-weight: 500;
        transition: all 0.3s ease;
        flex: 1;
        white-space: nowrap;
        --mdc-icon-size: 18px;
      }
      .elastic-trigger:hover {
        color: var(--primary-color);
      }
      .elastic-trigger.shrunk {
        flex: 0 0 42px;
        padding: 8px;
        background: var(--error-color, #db4437);
        color: var(--text-primary-color);
        border-radius: 0;
      }
      .elastic-trigger.shrunk ha-icon {
        transition: transform 0.3s ease;
        transform: rotate(45deg);
      }
      .elastic-trigger.shrunk span {
        display: none;
      }
      .elastic-trigger:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      .elastic-opts {
        display: flex;
        flex: 0;
        overflow: hidden;
        transition: flex 0.3s ease;
      }
      .elastic-opts.open {
        flex: 1;
      }
      .elastic-opt {
        flex: 1;
        padding: 8px 4px;
        border: none;
        border-left: 1px solid var(--divider-color);
        background: none;
        color: var(--primary-text-color);
        cursor: pointer;
        font-size: 0.78rem;
        font-family: inherit;
        font-weight: 500;
        transition: all 0.15s ease;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        --mdc-icon-size: 16px;
      }
      .elastic-opt:hover {
        background: var(--primary-color);
        color: var(--text-primary-color);
      }
      .elastic-opt.unnamed {
        flex: 0 0 42px;
      }
      .error {
        padding: 4px 12px;
        font-size: 0.8rem;
        color: var(--error-color, #db4437);
      }
      @keyframes pulse {
        0%,
        100% {
          opacity: 1;
        }
        50% {
          opacity: 0.5;
        }
      }
    `;
  }
}
