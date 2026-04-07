import { LitElement, html, css, type CSSResultGroup } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("bb-child-header")
export class ChildHeader extends LitElement {
  @property() public name = "";
  @property() public age = "";
  @property() public picture?: string;
  @property({ type: Boolean }) public compact = false;

  protected render() {
    return html`
      <div class="header ${this.compact ? "compact" : ""}">
        ${this.picture
          ? html`<img class="avatar" src=${this.picture} alt=${this.name} />`
          : html`<div class="avatar placeholder">
              <ha-icon icon="mdi:baby-face-outline"></ha-icon>
            </div>`}
        <div class="info">
          <div class="name">${this.name}</div>
          <div class="age">${this.age}</div>
        </div>
      </div>
    `;
  }

  static get styles(): CSSResultGroup {
    return css`
      :host {
        display: block;
      }
      .header {
        display: flex;
        align-items: center;
        gap: 12px;
        animation: fadeIn 0.3s ease;
      }
      .avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        object-fit: cover;
        flex-shrink: 0;
        transition: transform 0.2s ease;
      }
      .avatar:hover {
        transform: scale(1.05);
      }
      .placeholder {
        display: flex;
        align-items: center;
        justify-content: center;
        background: var(--primary-color);
        color: var(--text-primary-color);
        --mdc-icon-size: 28px;
      }
      .info {
        min-width: 0;
        flex: 1;
      }
      .name {
        font-size: 1.1rem;
        font-weight: 500;
        color: var(--primary-text-color);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      .age {
        font-size: 0.85rem;
        color: var(--secondary-text-color);
        margin-top: 1px;
      }
      .header.compact {
        gap: 8px;
        margin-bottom: 8px;
      }
      .header.compact .avatar {
        width: 32px;
        height: 32px;
      }
      .header.compact .placeholder {
        --mdc-icon-size: 20px;
      }
      .header.compact .name {
        font-size: 0.95rem;
      }
      .header.compact .age {
        font-size: 0.75rem;
      }
      @keyframes fadeIn {
        from {
          opacity: 0;
          transform: translateY(-4px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
    `;
  }
}
