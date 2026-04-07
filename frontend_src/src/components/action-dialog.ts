import { LitElement, html, css, nothing, type CSSResultGroup } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant, HassEntity } from "../types";
import { labelForServiceKey } from "../utils";

@customElement("bb-action-dialog")
export class ActionDialog extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;
  @property() public action = "";
  @property({ attribute: false }) public childEntity!: HassEntity;
  @property({ attribute: false }) public timers: HassEntity[] = [];
  @property({ attribute: false }) public selects: HassEntity[] = [];
  @property({ type: Number }) public initialTimerId?: number;
  @state() private _formData: Record<string, unknown> = {};
  @state() private _submitting = false;
  @state() private _error: string | null = null;
  private _initialTimerApplied = false;
  private _defaultsApplied = false;

  private _getServiceFields(): Record<string, unknown> {
    const svc = this.hass?.services?.babybuddy?.[this.action];
    if (!svc?.fields) return {};

    const fields = { ...svc.fields } as Record<
      string,
      Record<string, unknown>
    >;

    for (const [name, field] of Object.entries(fields)) {
      const sel = field.selector as Record<string, unknown> | undefined;
      if (!sel?.select) continue;

      const selectInfo = sel.select as Record<string, unknown>;
      if (
        selectInfo.options &&
        (selectInfo.options as unknown[]).length > 0
      )
        continue;

      const selectEntity = this.selects.find((s) => {
        const eid = s.entity_id;
        return eid.includes(name) || eid.endsWith(`_${name}`);
      });
      if (selectEntity) {
        const opts = selectEntity.attributes.options as string[] | undefined;
        if (opts) {
          fields[name] = {
            ...field,
            selector: {
              select: { ...selectInfo, options: opts },
            },
          };
        }
      }
    }

    return fields;
  }

  connectedCallback(): void {
    super.connectedCallback();
    this._onKeyDown = this._onKeyDown.bind(this);
    window.addEventListener("keydown", this._onKeyDown);
    this._initialTimerApplied = false;
    this._defaultsApplied = false;
  }

  protected updated(changedProps: Map<string, unknown>): void {
    super.updated(changedProps);

    const svcFields = this.hass?.services?.babybuddy?.[this.action]?.fields;
    const usesTimer = svcFields != null && "timer" in svcFields;

    if (!usesTimer && this._formData._selected_timer != null) {
      this._formData = { ...this._formData, _selected_timer: undefined };
      return;
    }

    if (!this._initialTimerApplied && this.initialTimerId != null && usesTimer) {
      const match = this.timers.find(
        (t) => (t.attributes.timer_id as number) === this.initialTimerId,
      );
      if (match) {
        this._formData = {
          ...this._formData,
          _selected_timer: this.initialTimerId,
        };
        this._initialTimerApplied = true;
      }
    }

    if (!this._defaultsApplied && this.action && svcFields) {
      this._defaultsApplied = true;
      const now = new Date();
      const hh = String(now.getHours()).padStart(2, "0");
      const mm = String(now.getMinutes()).padStart(2, "0");
      const nowTime = `${hh}:${mm}`;
      const todayDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;

      const defaults: Record<string, unknown> = {};
      for (const [name, field] of Object.entries(svcFields)) {
        const f = field as Record<string, unknown>;
        const sel = f.selector as Record<string, unknown> | undefined;
        if (f.default === "now" && sel?.time != null) {
          defaults[name] = nowTime;
        } else if (f.default === "today" && sel?.date != null) {
          defaults[name] = todayDate;
        }
      }
      if (Object.keys(defaults).length > 0) {
        this._formData = { ...defaults, ...this._formData };
      }
    }
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    window.removeEventListener("keydown", this._onKeyDown);
  }

  private _onKeyDown(e: KeyboardEvent): void {
    if (e.key === "Escape") this._close();
  }

  private _close(): void {
    this.dispatchEvent(
      new CustomEvent("bb-dialog-close", {
        bubbles: true,
        composed: true,
      }),
    );
  }

  private _updateField(name: string, value: unknown): void {
    this._formData = { ...this._formData, [name]: value };
  }

  private _activeExclusionGroups(
    fields: Record<string, unknown>,
  ): Set<string> {
    const groups = new Set<string>();
    const timerField = fields.timer as Record<string, unknown> | undefined;
    const timerExcGroup = timerField?.exclusion_group as string | undefined;
    if (this._formData._selected_timer != null && timerExcGroup) {
      groups.add(timerExcGroup);
    }
    return groups;
  }

  private _isFieldHidden(
    name: string,
    field: Record<string, unknown>,
    activeExcGroups: Set<string>,
  ): boolean {
    if (name === "entity_id" || field.hidden_in_card === true) return true;
    const eg = field.exclusion_group as string | undefined;
    if (eg && activeExcGroups.has(eg)) return true;
    const hwg = field.hidden_when_group as string | undefined;
    if (hwg && activeExcGroups.has(hwg)) return true;
    return false;
  }

  private _textColorFor(color: string): string {
    let c = color.replace("#", "");
    if (/^[0-9a-f]{3}$/i.test(c)) {
      c = c[0] + c[0] + c[1] + c[1] + c[2] + c[2];
    }
    if (!/^[0-9a-f]{6}$/i.test(c)) return "#000";
    const r = parseInt(c.substring(0, 2), 16) / 255;
    const g = parseInt(c.substring(2, 4), 16) / 255;
    const b = parseInt(c.substring(4, 6), 16) / 255;
    const luminance =
      0.2126 * (r <= 0.03928 ? r / 12.92 : ((r + 0.055) / 1.055) ** 2.4) +
      0.7152 * (g <= 0.03928 ? g / 12.92 : ((g + 0.055) / 1.055) ** 2.4) +
      0.0722 * (b <= 0.03928 ? b / 12.92 : ((b + 0.055) / 1.055) ** 2.4);
    return luminance > 0.179 ? "#000" : "#fff";
  }

  private async _submit(): Promise<void> {
    this._submitting = true;
    this._error = null;

    try {
      const data: Record<string, unknown> = { ...this._formData };

      if (this.childEntity) {
        data.entity_id = this.childEntity.entity_id;
      }

      const selectedTimerId = this._formData._selected_timer as
        | number
        | undefined;
      if (selectedTimerId != null) {
        data.timer = selectedTimerId;
      }
      delete data._selected_timer;

      const fields = this._getServiceFields();
      const activeExcGroups = this._activeExclusionGroups(fields);
      for (const [name, field] of Object.entries(fields)) {
        if (
          name !== "timer" &&
          this._isFieldHidden(name, field as Record<string, unknown>, activeExcGroups)
        ) {
          delete data[name];
        }
      }

      await this.hass.callService("babybuddy", this.action, data);
      this._close();
    } catch (err: unknown) {
      this._error =
        err instanceof Error ? err.message : "An error occurred";
    } finally {
      this._submitting = false;
    }
  }

  protected render() {
    const fields = this._getServiceFields();
    const serviceUsesTimer = "timer" in fields;
    const svc = this.hass?.services?.babybuddy?.[this.action];
    const title =
      (svc as { name?: string } | undefined)?.name ??
      labelForServiceKey(this.action);

    const activeExcGroups = this._activeExclusionGroups(fields);

    return html`
      <div class="overlay" @click=${this._close}>
        <div
          class="dialog"
          role="dialog"
          aria-modal="true"
          aria-label=${title}
          @click=${(e: Event) => e.stopPropagation()}
        >
          <div class="dialog-header">
            <span class="dialog-title">${title}</span>
            <button class="close-btn" @click=${this._close}>
              <ha-icon icon="mdi:close"></ha-icon>
            </button>
          </div>

          <div class="dialog-body">
            ${serviceUsesTimer && this.timers.length > 0
              ? html`
                  <div class="field">
                    <span>Use timer</span>
                    <div class="pill-group">
                      <button
                        type="button"
                        class="pill ${this._formData._selected_timer == null ? "active" : ""}"
                        @click=${() =>
                          this._updateField("_selected_timer", undefined)}
                      >
                        Manual
                      </button>
                      ${this.timers.map((t) => {
                        const tid = t.attributes.timer_id as number;
                        const tname =
                          (t.attributes.timer_name as string) ||
                          `Timer ${tid}`;
                        const active =
                          (this._formData._selected_timer as number) === tid;
                        return html`<button
                          type="button"
                          class="pill ${active ? "active" : ""}"
                          @click=${() =>
                            this._updateField("_selected_timer", tid)}
                        >
                          ${tname}
                        </button>`;
                      })}
                    </div>
                  </div>
                `
              : nothing}
            ${Object.entries(fields).map(([name, field]) =>
              this._renderField(
                name,
                field as Record<string, unknown>,
                activeExcGroups,
              ),
            )}
          </div>

          ${this._error
            ? html`<div class="error">${this._error}</div>`
            : nothing}

          <div class="dialog-footer">
            <button class="btn cancel" @click=${this._close}>Cancel</button>
            <button
              class="btn submit"
              @click=${this._submit}
              ?disabled=${this._submitting}
            >
              ${this._submitting ? "Saving..." : "Save"}
            </button>
          </div>
        </div>
      </div>
    `;
  }

  private _renderField(
    name: string,
    field: Record<string, unknown>,
    activeExcGroups: Set<string>,
  ) {
    if (this._isFieldHidden(name, field, activeExcGroups)) return nothing;

    const label =
      (field.name as string) ?? labelForServiceKey(name);
    const selector = field.selector as Record<string, unknown> | undefined;

    if (selector?.boolean != null) {
      const checked = this._formData[name] === true;
      return html`
        <div class="field">
          <span>${label}</span>
          <div class="pill-group">
            <button
              type="button"
              class="pill ${checked ? "active" : ""}"
              @click=${() => this._updateField(name, !checked)}
            >
              ${label}
            </button>
          </div>
        </div>
      `;
    }

    if (selector?.select) {
      const opts = ((selector.select as Record<string, unknown>)
        .options ?? []) as Array<
        string | { value: string; label: string; color?: string }
      >;
      const current = (this._formData[name] as string) ?? "";
      return html`
        <div class="field">
          <span>${label}</span>
          <div class="pill-group">
            ${opts.map((o) => {
              const val = typeof o === "string" ? o : o.value;
              const lbl = typeof o === "string" ? o : o.label;
              const color = typeof o === "object" ? o.color : undefined;
              const isActive = current === val;
              const pillStyle = color
                ? isActive
                  ? `background:${color};color:${this._textColorFor(color)};border-color:${color}`
                  : `background:${color}22;border-color:${color}44`
                : "";
              return html`<button
                type="button"
                class="pill ${isActive ? "active" : ""} ${color ? "color-pill" : ""}"
                style=${pillStyle}
                @click=${() =>
                  this._updateField(name, isActive ? "" : val)}
              >
                ${lbl}
              </button>`;
            })}
          </div>
        </div>
      `;
    }

    if (selector?.date != null) {
      return html`
        <label class="field">
          <span>${label}</span>
          <input
            type="date"
            .value=${(this._formData[name] as string) ?? ""}
            @input=${(e: Event) =>
              this._updateField(name, (e.target as HTMLInputElement).value)}
          />
        </label>
      `;
    }

    if (selector?.time != null) {
      return html`
        <label class="field">
          <span>${label}</span>
          <input
            type="time"
            .value=${(this._formData[name] as string) ?? ""}
            @input=${(e: Event) =>
              this._updateField(name, (e.target as HTMLInputElement).value)}
          />
        </label>
      `;
    }

    if (selector?.number != null) {
      const numOpts = selector.number as Record<string, unknown>;
      return html`
        <label class="field">
          <span>${label}</span>
          <input
            type="number"
            .value=${String(this._formData[name] ?? "")}
            min=${numOpts.min ?? nothing}
            max=${numOpts.max ?? nothing}
            step=${numOpts.step ?? "any"}
            @input=${(e: Event) => {
              const v = (e.target as HTMLInputElement).value;
              this._updateField(name, v === "" ? undefined : Number(v));
            }}
          />
        </label>
      `;
    }

    if (selector?.text != null) {
      const textOpts = selector.text as Record<string, unknown>;
      if (textOpts.multiline) {
        return html`
          <label class="field">
            <span>${label}</span>
            <textarea
              rows="3"
              .value=${(this._formData[name] as string) ?? ""}
              @input=${(e: Event) =>
                this._updateField(
                  name,
                  (e.target as HTMLTextAreaElement).value,
                )}
            ></textarea>
          </label>
        `;
      }
    }

    return html`
      <label class="field">
        <span>${label}</span>
        <input
          type="text"
          .value=${(this._formData[name] as string) ?? ""}
          @input=${(e: Event) =>
            this._updateField(
              name,
              (e.target as HTMLInputElement).value,
            )}
        />
      </label>
    `;
  }

  static get styles(): CSSResultGroup {
    return css`
      .overlay {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: flex-end;
        justify-content: center;
        z-index: 999;
        padding: 0;
        animation: fadeIn 0.2s ease;
      }
      @media (min-width: 500px) {
        .overlay {
          align-items: center;
          padding: 16px;
        }
      }
      .dialog {
        background: var(--card-background-color, var(--ha-card-background));
        border-radius: 16px 16px 0 0;
        width: 100%;
        max-width: 400px;
        max-height: 85vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        box-shadow: var(--ha-card-box-shadow, 0 -2px 16px rgba(0, 0, 0, 0.2));
        animation: slideUp 0.25s ease;
      }
      @media (min-width: 500px) {
        .dialog {
          border-radius: 16px;
          box-shadow: var(
            --ha-card-box-shadow,
            0 4px 24px rgba(0, 0, 0, 0.3)
          );
          animation: popIn 0.2s ease;
        }
      }
      .dialog-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px;
        border-bottom: 1px solid var(--divider-color);
      }
      .dialog-title {
        font-size: 1.1rem;
        font-weight: 500;
      }
      .close-btn {
        background: none;
        border: none;
        cursor: pointer;
        color: var(--secondary-text-color);
        padding: 4px;
        --mdc-icon-size: 20px;
      }
      .dialog-body {
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
        overflow-y: auto;
        flex: 1;
        min-height: 0;
      }
      .field {
        display: flex;
        flex-direction: column;
        gap: 4px;
        font-size: 0.9rem;
        color: var(--primary-text-color);
      }
      .pill-group {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
      }
      .pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 14px;
        border-radius: 20px;
        border: 1px solid var(--divider-color);
        background: var(--secondary-background-color);
        color: var(--primary-text-color);
        font-size: 0.85rem;
        font-family: inherit;
        cursor: pointer;
        transition: background 0.15s, border-color 0.15s;
      }
      .pill.active {
        background: var(--primary-color);
        color: var(--text-primary-color);
        border-color: var(--primary-color);
      }
      .pill.color-pill {
        transition: background 0.15s, border-color 0.15s, color 0.15s;
      }
      .field input[type="text"],
      .field input[type="date"],
      .field input[type="time"],
      .field input[type="number"],
      .field textarea {
        padding: 8px;
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        background: var(--secondary-background-color);
        color: var(--primary-text-color);
        font-size: 0.9rem;
        font-family: inherit;
      }
      .field textarea {
        resize: vertical;
        min-height: 60px;
      }
      .error {
        padding: 8px 16px;
        color: var(--error-color);
        font-size: 0.85rem;
      }
      .dialog-footer {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        padding: 12px 16px;
        border-top: 1px solid var(--divider-color);
      }
      .btn {
        padding: 8px 16px;
        border-radius: 8px;
        font-size: 0.9rem;
        font-family: inherit;
        cursor: pointer;
        border: none;
      }
      .cancel {
        background: none;
        color: var(--secondary-text-color);
      }
      .submit {
        background: var(--primary-color);
        color: var(--text-primary-color);
      }
      .submit:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      @keyframes slideUp {
        from { transform: translateY(100%); }
        to { transform: translateY(0); }
      }
      @keyframes popIn {
        from { opacity: 0; transform: scale(0.95); }
        to { opacity: 1; transform: scale(1); }
      }
    `;
  }
}
