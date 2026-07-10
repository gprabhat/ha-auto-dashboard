// Dashboard Studio: a sidebar panel for reordering, hiding, renaming and
// adding cards to the dashboards HA Auto Dashboard auto-generates - without
// those edits being lost the next time the integration rescans and
// regenerates. See custom_components/ha_auto_dashboard/dashboard/overrides.py
// for the backend half of this (the override merge + stable card-id scheme
// this file mirrors on the client).
//
// No build step: this is a hand-written ES module, vendoring its two small
// dependencies (Lit, SortableJS) locally under vendor/ rather than pulling
// them from a CDN at runtime, so it keeps working on offline/local HA
// instances.
import { LitElement, html, css, nothing } from "./vendor/lit-core.min.js";
import Sortable from "./vendor/sortable.esm.js";

const CMD_GET_STATE = "ha_auto_dashboard/studio/get_state";
const CMD_SAVE_OVERRIDES = "ha_auto_dashboard/studio/save_overrides";
const CMD_RESET = "ha_auto_dashboard/studio/reset";

// Mirrors dashboard/overrides.py::_iter_containers: a view's top-level
// `cards` list, plus the `cards` list of any top-level `grid` card. No view
// this integration builds nests a grid inside another grid.
function containersOf(view) {
  const containers = [{ key: "root", title: null, cards: view.cards }];
  for (const card of view.cards) {
    if (card.type === "grid") {
      containers.push({ key: card._studio_id, title: card.title || null, cards: card.cards });
    }
  }
  return containers;
}

function cardLabel(card) {
  if (card.name) return card.name;
  if (card.entity) return card.entity;
  if (card.title) return card.title;
  return card.type;
}

function cardIcon(card) {
  return card.icon || null;
}

class HaAutoDashboardStudioPanel extends LitElement {
  static properties = {
    hass: { type: Object },
    narrow: { type: Boolean },
    panel: { type: Object },
    _state: { state: true },
    _error: { state: true },
    _activeDashboard: { state: true },
    _activeViewPath: { state: true },
    _overrides: { state: true },
    _dirty: { state: true },
    _saving: { state: true },
    _editingCardId: { state: true },
    _addDialogOpen: { state: true },
    _addFilter: { state: true },
  };

  constructor() {
    super();
    this._state = null;
    this._error = null;
    this._activeDashboard = null;
    this._activeViewPath = null;
    this._overrides = { cards: {}, added_cards: [] };
    this._dirty = false;
    this._saving = false;
    this._editingCardId = null;
    this._addDialogOpen = false;
    this._addFilter = "";
    this._loading = false;
  }

  connectedCallback() {
    super.connectedCallback();
    if (this.hass) this._load();
  }

  updated(changed) {
    super.updated(changed);
    // `hass` is set by HA's panel-resolver as a property, which can land
    // before or after connectedCallback depending on how the panel was
    // navigated to - only fetch once we actually have it and haven't yet.
    if (changed.has("hass") && this.hass && !this._state && !this._loading) {
      this._load();
    }
    if (changed.has("_state") || changed.has("_activeViewPath") || changed.has("_overrides")) {
      this._attachSortable();
    }
  }

  async _load() {
    this._loading = true;
    try {
      const result = await this.hass.connection.sendMessagePromise({ type: CMD_GET_STATE });
      this._applyState(result);
    } catch (err) {
      this._error = err.message || String(err);
    } finally {
      this._loading = false;
    }
  }

  _applyState(result) {
    this._state = result;
    this._overrides = {
      cards: { ...(result.overrides.cards || {}) },
      added_cards: [...(result.overrides.added_cards || [])],
    };
    this._dirty = false;
    this._error = null;
    if (!this._activeDashboard || !result.dashboards[this._activeDashboard]) {
      this._activeDashboard = Object.keys(result.dashboards)[0] || null;
    }
    const views = this._activeDashboard ? result.dashboards[this._activeDashboard].views : [];
    if (!this._activeViewPath || !views.some((v) => v.path === this._activeViewPath)) {
      this._activeViewPath = views[0]?.path || null;
    }
  }

  _activeView() {
    if (!this._state || !this._activeDashboard) return null;
    const dashboard = this._state.dashboards[this._activeDashboard];
    return dashboard?.views.find((v) => v.path === this._activeViewPath) || null;
  }

  _markDirty() {
    this._dirty = true;
    this.requestUpdate();
  }

  _toggleHidden(cardId) {
    const current = this._overrides.cards[cardId] || {};
    this._overrides.cards = {
      ...this._overrides.cards,
      [cardId]: { ...current, hidden: !current.hidden },
    };
    this._markDirty();
  }

  _startEdit(cardId) {
    this._editingCardId = cardId;
  }

  _saveEdit(cardId, name, icon) {
    const current = this._overrides.cards[cardId] || {};
    this._overrides.cards = {
      ...this._overrides.cards,
      [cardId]: { ...current, name: name || undefined, icon: icon || undefined },
    };
    this._editingCardId = null;
    this._markDirty();
  }

  _reorderContainer(cardIds) {
    const updated = { ...this._overrides.cards };
    cardIds.forEach((id, index) => {
      updated[id] = { ...(updated[id] || {}), order: index };
    });
    this._overrides.cards = updated;
    this._markDirty();
  }

  _addEntity(entityId) {
    if (!this._activeDashboard || !this._activeViewPath) return;
    const already = this._overrides.added_cards.some(
      (a) =>
        a.dashboard === this._activeDashboard &&
        a.view === this._activeViewPath &&
        a.entity_id === entityId
    );
    if (!already) {
      this._overrides.added_cards = [
        ...this._overrides.added_cards,
        { dashboard: this._activeDashboard, view: this._activeViewPath, entity_id: entityId },
      ];
      this._markDirty();
    }
    this._addDialogOpen = false;
    this._addFilter = "";
  }

  async _save() {
    this._saving = true;
    try {
      const result = await this.hass.connection.sendMessagePromise({
        type: CMD_SAVE_OVERRIDES,
        overrides: this._overrides,
      });
      this._applyState(result);
    } catch (err) {
      this._error = err.message || String(err);
    } finally {
      this._saving = false;
    }
  }

  async _resetAll() {
    this._saving = true;
    try {
      const result = await this.hass.connection.sendMessagePromise({ type: CMD_RESET });
      this._applyState(result);
    } catch (err) {
      this._error = err.message || String(err);
    } finally {
      this._saving = false;
    }
  }

  _discard() {
    if (this._state) this._applyState(this._state);
  }

  _attachSortable() {
    this.updateComplete.then(() => {
      const lists = this.renderRoot.querySelectorAll("[data-sortable-container]");
      lists.forEach((list) => {
        if (list._sortableInstance) return;
        list._sortableInstance = new Sortable(list, {
          handle: ".drag-handle",
          animation: 150,
          onEnd: () => {
            const ids = Array.from(list.children).map((el) => el.dataset.cardId);
            this._reorderContainer(ids);
          },
        });
      });
    });
  }

  render() {
    if (this._error) {
      return html`<div class="wrap"><ha-alert alert-type="error">${this._error}</ha-alert></div>`;
    }
    if (!this._state) {
      return html`<div class="wrap">Loading…</div>`;
    }

    const view = this._activeView();
    const dashboards = this._state.dashboards;

    return html`
      <div class="toolbar">
        <div class="tabs">
          ${Object.entries(dashboards).map(
            ([slug, d]) => html`
              <button
                class="tab ${slug === this._activeDashboard ? "active" : ""}"
                @click=${() => {
                  this._activeDashboard = slug;
                  this._activeViewPath = d.views[0]?.path || null;
                }}
              >
                <ha-icon icon=${d.icon}></ha-icon>
                ${d.title}
              </button>
            `
          )}
        </div>
        <div class="actions">
          ${this._dirty
            ? html`
                <button class="btn" @click=${this._discard}>Discard</button>
                <button class="btn primary" ?disabled=${this._saving} @click=${this._save}>
                  ${this._saving ? "Saving…" : "Save"}
                </button>
              `
            : html`<button class="btn" @click=${this._resetAll}>Reset all overrides</button>`}
        </div>
      </div>

      ${dashboards[this._activeDashboard]
        ? html`
            <div class="view-tabs">
              ${dashboards[this._activeDashboard].views.map(
                (v) => html`
                  <button
                    class="view-tab ${v.path === this._activeViewPath ? "active" : ""}"
                    @click=${() => (this._activeViewPath = v.path)}
                  >
                    ${v.title}
                  </button>
                `
              )}
            </div>
          `
        : nothing}

      ${view ? this._renderView(view) : html`<div class="wrap">No view selected.</div>`}

      <button class="fab" title="Add entity" @click=${() => (this._addDialogOpen = true)}>+</button>

      ${this._addDialogOpen ? this._renderAddDialog() : nothing}
    `;
  }

  _renderView(view) {
    // The root container's own card list includes structural cards this
    // v1 editor doesn't manage directly (title/chips/map/logbook/grid
    // sections) - grid cards get rendered as their own titled section
    // below instead of a second time as a leaf row here, and the other
    // structural types are simply not addressable yet (a known v1 limit,
    // consistent with dashboard/overrides.py's card_id scheme only
    // giving first-class ids to entity cards, area cards, and grids).
    const containers = containersOf(view).map((container) =>
      container.key === "root"
        ? { ...container, cards: container.cards.filter((card) => !!card.entity) }
        : container
    );
    return html`
      <div class="wrap">
        ${containers.map(
          (container) => html`
            ${container.title ? html`<h3>${container.title}</h3>` : nothing}
            <div class="card-list" data-sortable-container>
              ${container.cards.map((card) => this._renderCard(card))}
            </div>
          `
        )}
        ${containers.every((c) => c.cards.length === 0)
          ? html`<p class="empty">Nothing in this view.</p>`
          : nothing}
      </div>
    `;
  }

  _renderCard(card) {
    const id = card._studio_id;
    const override = this._overrides.cards[id] || {};
    const editing = this._editingCardId === id;

    return html`
      <div class="card-row" data-card-id=${id}>
        <span class="drag-handle" title="Drag to reorder">⠿</span>
        ${cardIcon(card) ? html`<ha-icon icon=${cardIcon(card)}></ha-icon>` : nothing}
        <span class="label">${cardLabel(card)}</span>
        <span class="type-badge">${card.type.replace("custom:mushroom-", "").replace("-card", "")}</span>
        <span class="spacer"></span>
        <button class="icon-btn" title="Rename / re-icon" @click=${() => this._startEdit(id)}>✏️</button>
        <button class="icon-btn" title=${override.hidden ? "Show" : "Hide"} @click=${() => this._toggleHidden(id)}>
          ${override.hidden ? "🚫" : "👁"}
        </button>
      </div>
      ${editing ? this._renderEditForm(id, card, override) : nothing}
    `;
  }

  _renderEditForm(id, card, override) {
    return html`
      <div class="edit-form">
        <input
          type="text"
          placeholder="Name"
          .value=${override.name || ""}
          id="edit-name-${id}"
        />
        <input
          type="text"
          placeholder="mdi:icon-name"
          .value=${override.icon || ""}
          id="edit-icon-${id}"
        />
        <button
          class="btn primary"
          @click=${() => {
            const name = this.renderRoot.getElementById(`edit-name-${id}`).value;
            const icon = this.renderRoot.getElementById(`edit-icon-${id}`).value;
            this._saveEdit(id, name, icon);
          }}
        >
          Apply
        </button>
        <button class="btn" @click=${() => (this._editingCardId = null)}>Cancel</button>
      </div>
    `;
  }

  _renderAddDialog() {
    const view = this._activeView();
    const placedEntityIds = new Set();
    if (view) {
      for (const container of containersOf(view)) {
        for (const card of container.cards) {
          if (card.entity) placedEntityIds.add(card.entity);
        }
      }
    }
    const filter = this._addFilter.toLowerCase();
    const candidates = (this._state.entities || [])
      .filter((e) => !placedEntityIds.has(e.entity_id))
      .filter((e) => !filter || e.entity_id.toLowerCase().includes(filter) || e.name.toLowerCase().includes(filter))
      .slice(0, 100);

    return html`
      <div class="dialog-backdrop" @click=${() => (this._addDialogOpen = false)}>
        <div class="dialog" @click=${(e) => e.stopPropagation()}>
          <h3>Add an entity to ${view?.title || "this view"}</h3>
          <input
            type="text"
            placeholder="Search entities…"
            .value=${this._addFilter}
            @input=${(e) => (this._addFilter = e.target.value)}
          />
          <div class="candidate-list">
            ${candidates.map(
              (e) => html`
                <button class="candidate" @click=${() => this._addEntity(e.entity_id)}>
                  <strong>${e.name}</strong>
                  <span class="muted">${e.entity_id}</span>
                </button>
              `
            )}
            ${candidates.length === 0 ? html`<p class="empty">No matching entities.</p>` : nothing}
          </div>
          <button class="btn" @click=${() => (this._addDialogOpen = false)}>Close</button>
        </div>
      </div>
    `;
  }

  static styles = css`
    :host {
      display: block;
      padding: 16px;
      font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
      color: var(--primary-text-color);
      background: var(--primary-background-color);
      min-height: 100vh;
      box-sizing: border-box;
    }
    .wrap {
      padding: 8px 0 96px 0;
    }
    .toolbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
      border-bottom: 1px solid var(--divider-color);
      padding-bottom: 8px;
    }
    .tabs,
    .view-tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }
    .view-tabs {
      margin: 12px 0;
    }
    .tab,
    .view-tab,
    .btn {
      border: 1px solid var(--divider-color);
      background: var(--card-background-color);
      color: var(--primary-text-color);
      border-radius: 8px;
      padding: 6px 12px;
      cursor: pointer;
      font-size: 0.9em;
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }
    .tab.active,
    .view-tab.active {
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
      border-color: var(--primary-color);
    }
    .btn.primary {
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
      border-color: var(--primary-color);
    }
    .btn[disabled] {
      opacity: 0.6;
      cursor: default;
    }
    h3 {
      margin: 16px 0 8px 0;
      font-size: 1em;
      color: var(--secondary-text-color);
    }
    .card-list {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .card-row {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 10px;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      background: var(--card-background-color);
    }
    .drag-handle {
      cursor: grab;
      color: var(--secondary-text-color);
    }
    .label {
      font-weight: 500;
    }
    .type-badge {
      font-size: 0.75em;
      color: var(--secondary-text-color);
      background: var(--secondary-background-color, rgba(127, 127, 127, 0.15));
      border-radius: 4px;
      padding: 2px 6px;
    }
    .spacer {
      flex: 1;
    }
    .icon-btn {
      border: none;
      background: none;
      cursor: pointer;
      font-size: 1em;
      padding: 4px;
    }
    .edit-form {
      display: flex;
      gap: 8px;
      align-items: center;
      padding: 8px 10px 12px 34px;
    }
    .edit-form input {
      flex: 1;
      padding: 4px 8px;
      border: 1px solid var(--divider-color);
      border-radius: 4px;
      background: var(--card-background-color);
      color: var(--primary-text-color);
    }
    .empty {
      color: var(--secondary-text-color);
      font-style: italic;
    }
    .fab {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
      border: none;
      font-size: 1.6em;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    .dialog-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10;
    }
    .dialog {
      background: var(--card-background-color);
      color: var(--primary-text-color);
      border-radius: 12px;
      padding: 16px;
      width: min(480px, 90vw);
      max-height: 80vh;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .dialog input {
      padding: 8px;
      border-radius: 4px;
      border: 1px solid var(--divider-color);
      background: var(--primary-background-color);
      color: var(--primary-text-color);
    }
    .candidate-list {
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .candidate {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      border: none;
      background: none;
      color: var(--primary-text-color);
      text-align: left;
      padding: 6px 8px;
      border-radius: 4px;
      cursor: pointer;
    }
    .candidate:hover {
      background: var(--secondary-background-color, rgba(127, 127, 127, 0.15));
    }
    .muted {
      font-size: 0.8em;
      color: var(--secondary-text-color);
    }
  `;
}

customElements.define("ha-auto-dashboard-studio-panel", HaAutoDashboardStudioPanel);
