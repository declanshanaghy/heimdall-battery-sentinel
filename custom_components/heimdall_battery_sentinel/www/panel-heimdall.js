/**
 * Heimdall Battery Sentinel — Custom Sidebar Panel
 *
 * Plain JavaScript module (no TypeScript/Lit/bundler required).
 * Registered as a custom sidebar panel by the integration's async_setup_entry.
 *
 * Architecture: ADR-001 (custom panel), ADR-002 (event-driven), ADR-003 (WebSocket)
 *
 * Features:
 *  - Tabs: "Low Battery" and "Unavailable"
 *  - Sortable table headers
 *  - Infinite scroll (page size 100)
 *  - WebSocket: heimdall/summary, heimdall/list, heimdall/subscribe
 *  - Handles dataset invalidation (ADR-008)
 */

(function () {
  "use strict";

  const DOMAIN = "heimdall_battery_sentinel";
  const WS_SUMMARY = "heimdall/summary";
  const WS_LIST = "heimdall/list";
  const WS_SUBSCRIBE = "heimdall/subscribe";

  const TAB_LOW_BATTERY = "low_battery";
  const TAB_UNAVAILABLE = "unavailable";

  const DEFAULT_SORT = {
    [TAB_LOW_BATTERY]: { by: "battery_level", dir: "asc" },
    [TAB_UNAVAILABLE]: { by: "friendly_name", dir: "asc" },
  };

  const COLUMNS = {
    [TAB_LOW_BATTERY]: [
      { key: "friendly_name", label: "Entity" },
      { key: "battery_level", label: "Battery" },
      { key: "area", label: "Area" },
      { key: "manufacturer", label: "Manufacturer" },
    ],
    [TAB_UNAVAILABLE]: [
      { key: "friendly_name", label: "Entity" },
      { key: "area", label: "Area" },
      { key: "manufacturer", label: "Manufacturer" },
      { key: "updated_at", label: "Since" },
    ],
  };

  /**
   * HeimdallPanel — Custom HTML Element registered as <heimdall-panel>.
   */
  class HeimdallPanel extends HTMLElement {
    constructor() {
      super();
      this._hass = null;
      this._ws = null;
      this._subscriptionId = null;
      this._shadow = this.attachShadow({ mode: "open" });

      // UI state
      this._activeTab = TAB_LOW_BATTERY;
      this._summary = { low_battery_count: 0, unavailable_count: 0, threshold: 15 };
      this._rows = { [TAB_LOW_BATTERY]: [], [TAB_UNAVAILABLE]: [] };
      this._sort = { ...DEFAULT_SORT };
      this._loading = false;
      this._offset = { [TAB_LOW_BATTERY]: 0, [TAB_UNAVAILABLE]: 0 };
      this._datasetVersion = { [TAB_LOW_BATTERY]: null, [TAB_UNAVAILABLE]: null };
      this._end = { [TAB_LOW_BATTERY]: false, [TAB_UNAVAILABLE]: false };
    }

    set hass(hass) {
      this._hass = hass;
      if (!this._ws) {
        this._initWebSocket();
      }
    }

    connectedCallback() {
      this._render();
    }

    // ── WebSocket Lifecycle ───────────────────────────────────────────────────

    _initWebSocket() {
      if (!this._hass || !this._hass.connection) return;
      this._ws = this._hass.connection;
      this._loadSummary();
      this._loadPage(this._activeTab, true);
      this._subscribe();
    }

    async _loadSummary() {
      try {
        const result = await this._ws.sendMessagePromise({ type: WS_SUMMARY });
        this._summary = result;
        this._updateTabCounts();
      } catch (err) {
        console.error("[HeimdallPanel] Failed to load summary:", err);
      }
    }

    async _loadPage(tab, reset = false) {
      if (this._loading) return;
      if (!reset && this._end[tab]) return;

      this._loading = true;

      if (reset) {
        this._rows[tab] = [];
        this._offset[tab] = 0;
        this._end[tab] = false;
      }

      const sort = this._sort[tab];
      try {
        const result = await this._ws.sendMessagePromise({
          type: WS_LIST,
          tab,
          sort_by: sort.by,
          sort_dir: sort.dir,
          offset: this._offset[tab],
          dataset_version: this._datasetVersion[tab],
        });

        if (result.invalidated && this._offset[tab] !== 0) {
          // Dataset changed — restart from page 0
          this._loadPage(tab, true);
          return;
        }

        this._datasetVersion[tab] = result.dataset_version;
        this._rows[tab] = [...this._rows[tab], ...result.rows];
        this._offset[tab] = result.next_offset || this._offset[tab] + result.rows.length;
        this._end[tab] = result.end;
        this._renderTable();
      } catch (err) {
        console.error("[HeimdallPanel] Failed to load page:", err);
      } finally {
        this._loading = false;
      }
    }

    async _subscribe() {
      try {
        await this._ws.subscribeMessage(
          (event) => this._handleSubscriptionEvent(event),
          { type: WS_SUBSCRIBE }
        );
      } catch (err) {
        console.error("[HeimdallPanel] Failed to subscribe:", err);
      }
    }

    _handleSubscriptionEvent(event) {
      const { type, tab } = event;

      if (type === "summary") {
        this._summary = {
          low_battery_count: event.low_battery_count,
          unavailable_count: event.unavailable_count,
          threshold: event.threshold,
        };
        this._updateTabCounts();
        return;
      }

      if (type === "invalidated") {
        // Full refresh needed
        this._datasetVersion[tab] = null;
        this._loadPage(tab, true);
        return;
      }

      if (type === "upsert" && event.row) {
        const rows = this._rows[tab];
        const idx = rows.findIndex((r) => r.entity_id === event.row.entity_id);
        if (idx >= 0) {
          rows[idx] = event.row;
        } else {
          rows.push(event.row);
        }
        if (tab === this._activeTab) this._renderTable();
        return;
      }

      if (type === "remove" && event.entity_id) {
        this._rows[tab] = this._rows[tab].filter(
          (r) => r.entity_id !== event.entity_id
        );
        if (tab === this._activeTab) this._renderTable();
      }
    }

    // ── Rendering ─────────────────────────────────────────────────────────────

    _render() {
      this._shadow.innerHTML = `
        <style>
          :host { display: block; padding: 16px; font-family: var(--paper-font-body1_-_font-family, sans-serif); }
          .tabs { display: flex; gap: 8px; margin-bottom: 16px; }
          .tab-btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            background: var(--secondary-background-color, #f0f0f0);
            font-size: 14px;
          }
          .tab-btn.active { background: var(--primary-color, #03a9f4); color: white; }
          table { width: 100%; border-collapse: collapse; }
          th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid var(--divider-color, #e0e0e0); }
          th { cursor: pointer; user-select: none; font-weight: 600; background: var(--table-header-background-color, #fafafa); }
          th:hover { background: var(--secondary-background-color, #f0f0f0); }
          .sort-icon { margin-left: 4px; font-size: 10px; }
          a { color: var(--primary-color, #03a9f4); text-decoration: none; }
          a:hover { text-decoration: underline; }
          .severity-red { color: #d32f2f; }
          .severity-orange { color: #f57c00; }
          .severity-yellow { color: #fbc02d; }
          .loading { text-align: center; padding: 24px; color: var(--secondary-text-color, #888); }
          .end-message { text-align: center; padding: 8px; color: var(--secondary-text-color, #888); font-size: 12px; }
          #sentinel { height: 1px; }
        </style>
        <div class="tabs" id="tab-bar"></div>
        <div id="table-container"></div>
        <div id="sentinel"></div>
      `;

      this._renderTabs();
      this._renderTable();
      this._setupScrollObserver();
    }

    _renderTabs() {
      const tabBar = this._shadow.getElementById("tab-bar");
      if (!tabBar) return;
      const tabs = [
        { id: TAB_LOW_BATTERY, label: `Low Battery (${this._summary.low_battery_count})` },
        { id: TAB_UNAVAILABLE, label: `Unavailable (${this._summary.unavailable_count})` },
      ];
      tabBar.innerHTML = tabs
        .map(
          (t) =>
            `<button class="tab-btn${t.id === this._activeTab ? " active" : ""}" data-tab="${t.id}">${t.label}</button>`
        )
        .join("");
      tabBar.querySelectorAll(".tab-btn").forEach((btn) => {
        btn.addEventListener("click", () => this._switchTab(btn.dataset.tab));
      });
    }

    _renderTable() {
      const container = this._shadow.getElementById("table-container");
      if (!container) return;

      const tab = this._activeTab;
      const cols = COLUMNS[tab];
      const rows = this._rows[tab];
      const sort = this._sort[tab];

      const headerRow = cols
        .map((col) => {
          const isActive = sort.by === col.key;
          const icon = isActive ? (sort.dir === "asc" ? "▲" : "▼") : "";
          return `<th data-col="${col.key}">${col.label}<span class="sort-icon">${icon}</span></th>`;
        })
        .join("");

      const bodyRows = rows
        .map((row) => {
          const cells = cols.map((col) => {
            if (col.key === "friendly_name") {
              const href = `/config/entities/entity/${row.entity_id}`;
              return `<td><a href="${href}" target="_blank">${this._esc(row.friendly_name || row.entity_id)}</a></td>`;
            }
            if (col.key === "battery_level") {
              const sevClass = row.severity ? `severity-${row.severity}` : "";
              return `<td class="${sevClass}">${this._esc(row.battery_display || "")}</td>`;
            }
            if (col.key === "updated_at" && row.updated_at) {
              return `<td>${new Date(row.updated_at).toLocaleString()}</td>`;
            }
            return `<td>${this._esc(row[col.key] || "")}</td>`;
          });
          return `<tr>${cells.join("")}</tr>`;
        })
        .join("");

      container.innerHTML = `
        <table>
          <thead><tr>${headerRow}</tr></thead>
          <tbody>${bodyRows}</tbody>
        </table>
        ${this._loading ? '<div class="loading">Loading…</div>' : ""}
        ${this._end[tab] && rows.length > 0 ? '<div class="end-message">All entities loaded</div>' : ""}
      `;

      // Attach sort click handlers
      container.querySelectorAll("th[data-col]").forEach((th) => {
        th.addEventListener("click", () => this._onSortClick(th.dataset.col));
      });
    }

    _updateTabCounts() {
      const tabBar = this._shadow.getElementById("tab-bar");
      if (!tabBar) return;
      tabBar.querySelectorAll(".tab-btn").forEach((btn) => {
        const tab = btn.dataset.tab;
        const count =
          tab === TAB_LOW_BATTERY
            ? this._summary.low_battery_count
            : this._summary.unavailable_count;
        const label = tab === TAB_LOW_BATTERY ? "Low Battery" : "Unavailable";
        btn.textContent = `${label} (${count})`;
      });
    }

    _setupScrollObserver() {
      const sentinel = this._shadow.getElementById("sentinel");
      if (!sentinel || !window.IntersectionObserver) return;
      const observer = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting) {
            this._loadPage(this._activeTab, false);
          }
        },
        { threshold: 0.1 }
      );
      observer.observe(sentinel);
    }

    // ── Event Handlers ────────────────────────────────────────────────────────

    _switchTab(tab) {
      if (tab === this._activeTab) return;
      this._activeTab = tab;
      this._renderTabs();
      this._renderTable();
      // Load first page if not loaded yet
      if (this._rows[tab].length === 0) {
        this._loadPage(tab, true);
      }
    }

    _onSortClick(col) {
      const tab = this._activeTab;
      const sort = this._sort[tab];
      if (sort.by === col) {
        sort.dir = sort.dir === "asc" ? "desc" : "asc";
      } else {
        sort.by = col;
        sort.dir = "asc";
      }
      this._loadPage(tab, true);
    }

    // ── Utilities ─────────────────────────────────────────────────────────────

    _esc(str) {
      return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }
  }

  // Register the custom element
  if (!customElements.get("heimdall-panel")) {
    customElements.define("heimdall-panel", HeimdallPanel);
  }
})();
