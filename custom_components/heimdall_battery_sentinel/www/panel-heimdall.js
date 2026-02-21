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
  const STORAGE_KEY = "heimdall_active_tab";

  const DEFAULT_SORT = {
    [TAB_LOW_BATTERY]: { by: "battery_level", dir: "asc" },
    [TAB_UNAVAILABLE]: { by: "friendly_name", dir: "asc" },
  };

  const COLUMNS = {
    [TAB_LOW_BATTERY]: [
      { key: "friendly_name", label: "Entity" },
      { key: "battery_level", label: "Battery" },
      { key: "model", label: "Model" },
      { key: "area", label: "Area" },
      { key: "manufacturer", label: "Manufacturer" },
    ],
    [TAB_UNAVAILABLE]: [
      { key: "friendly_name", label: "Entity" },
      { key: "model", label: "Model" },
      { key: "area", label: "Area" },
      { key: "manufacturer", label: "Manufacturer" },
      { key: "updated_at", label: "Since" },
    ],
  };

  /**
   * HeimdallPanel — Custom HTML Element registered as <heimdall-panel>.
   *
   * Manages tabbed interface, WebSocket communication, and real-time data display.
   */
  class HeimdallPanel extends HTMLElement {
    /**
     * Initialize HeimdallPanel with empty state.
     */
    constructor() {
      super();
      /** @type {Object|null} Home Assistant instance. */
      this._hass = null;
      /** @type {Object|null} Home Assistant WebSocket connection. */
      this._ws = null;
      /** @type {string|null} Active subscription ID. */
      this._subscriptionId = null;
      /** @type {ShadowRoot} Shadow DOM root for encapsulation. */
      this._shadow = this.attachShadow({ mode: "open" });

      // UI state
      /** @type {string} Currently active tab ("low_battery" or "unavailable"). */
      try {
        this._activeTab = (localStorage.getItem(STORAGE_KEY) === TAB_UNAVAILABLE) ? TAB_UNAVAILABLE : TAB_LOW_BATTERY;
      } catch (e) {
        // Private browsing mode or localStorage unavailable
        this._activeTab = TAB_LOW_BATTERY;
      }
      /** @type {Object} Summary data: low_battery_count, unavailable_count, threshold. */
      this._summary = { low_battery_count: 0, unavailable_count: 0, threshold: 15 };
      /** @type {Object<string, Array>} Cached rows by tab. */
      this._rows = { [TAB_LOW_BATTERY]: [], [TAB_UNAVAILABLE]: [] };
      /** @type {Object<string, Object>} Sort state by tab. */
      this._sort = { ...DEFAULT_SORT };
      /** @type {boolean} True while loading a page. */
      this._loading = false;
      /** @type {Object<string, number>} Current page offset by tab. */
      this._offset = { [TAB_LOW_BATTERY]: 0, [TAB_UNAVAILABLE]: 0 };
      /** @type {Object<string, string|null>} Dataset version by tab for invalidation detection. */
      this._datasetVersion = { [TAB_LOW_BATTERY]: null, [TAB_UNAVAILABLE]: null };
      /** @type {Object<string, boolean>} True when all rows for tab are loaded. */
      this._end = { [TAB_LOW_BATTERY]: false, [TAB_UNAVAILABLE]: false };
    }

    /**
     * Set Home Assistant instance (called by HA when panel loads).
     * @param {Object} hass - Home Assistant instance.
     */
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
      if (!this._hass || !this._hass.connection) {
        console.warn("[HeimdallPanel] Home Assistant connection not available");
        return;
      }
      this._ws = this._hass.connection;
      this._loadSummary();
      this._loadPage(this._activeTab, true);
      this._subscribe();
    }

    /**
     * Wraps a WebSocket message promise with a 10s timeout.
     * @param {Promise} promise - The promise to wrap.
     * @param {string} operation - Description of the operation for error messaging.
     * @returns {Promise} Promise that rejects after 10s if not resolved.
     */
    _withTimeout(promise, operation) {
      return Promise.race([
        promise,
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error(`Timeout: ${operation} exceeded 10s`)), 10000)
        ),
      ]);
    }

    async _loadSummary() {
      try {
        const result = await this._withTimeout(
          this._ws.sendMessagePromise({ type: WS_SUMMARY }),
          "Load summary"
        );
        this._summary = result;
        this._updateTabCounts();
      } catch (err) {
        console.error("[HeimdallPanel] Failed to load summary:", err);
        this._showError("Failed to load battery status");
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
        const result = await this._withTimeout(
          this._ws.sendMessagePromise({
            type: WS_LIST,
            tab,
            sort_by: sort.by,
            sort_dir: sort.dir,
            offset: this._offset[tab],
            dataset_version: this._datasetVersion[tab],
          }),
          `Load ${tab} page`
        );

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
        this._showError(`Failed to load ${tab} data`);
      } finally {
        this._loading = false;
      }
    }

    async _subscribe() {
      try {
        await this._withTimeout(
          this._ws.subscribeMessage(
            (event) => this._handleSubscriptionEvent(event),
            { type: WS_SUBSCRIBE }
          ),
          "Subscribe to updates"
        );
      } catch (err) {
        console.error("[HeimdallPanel] Failed to subscribe:", err);
        this._showError("Failed to subscribe to live updates");
      }
    }

    /**
     * Display an error message to the user in the panel.
     * @param {string} message - Error message to display.
     */
    _showError(message) {
      const errorEl = document.createElement("div");
      errorEl.style.cssText = `
        background-color: #ffebee;
        border-left: 4px solid #f44336;
        color: #b71c1c;
        padding: 12px;
        margin: 12px 0;
        border-radius: 2px;
        font-size: 14px;
      `;
      errorEl.textContent = message;
      
      const container = this._shadow.querySelector("main");
      if (container) {
        container.insertBefore(errorEl, container.firstChild);
        setTimeout(() => errorEl.remove(), 5000); // Auto-remove after 5s
      }
    }

    _handleSubscriptionEvent(event) {
      const { type, tab } = event;

      if (
        (type === "invalidated" || type === "upsert" || type === "remove") &&
        tab !== TAB_LOW_BATTERY &&
        tab !== TAB_UNAVAILABLE
      ) {
        this._showError(`Invalid tab: ${tab}`);
        return;
      }

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
          
          /* Typography Design Tokens */
          --typography-h6: { font-size: 20px; font-weight: 600; line-height: 1.3; };
          --typography-subtitle1: { font-size: 16px; font-weight: 500; line-height: 1.4; };
          --typography-body1: { font-size: 14px; font-weight: 400; line-height: 1.5; };
          --typography-caption: { font-size: 12px; font-weight: 400; line-height: 1.4; };

          .tabs { display: flex; gap: 8px; margin-bottom: 16px; }
          .tab-btn {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            background: var(--secondary-background-color, #f0f0f0);
            font-size: 14px;
            font-weight: 400;
          }
          .tab-btn:focus-visible {
            outline: 2px solid var(--primary-color, #03a9f4);
            outline-offset: 2px;
          }
          .tab-btn.active { background: var(--primary-color, #03a9f4); color: white; }
          
          table {
            width: 100%;
            border-collapse: collapse;
          }
          th, td {
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid var(--divider-color, #e0e0e0);
          }
          th {
            cursor: pointer;
            user-select: none;
            font-weight: 600;
            font-size: 14px;
            background: var(--table-header-background-color, #fafafa);
          }
          th:hover { background: var(--secondary-background-color, #f0f0f0); }
          th:focus-visible {
            outline: 2px solid var(--primary-color, #03a9f4);
            outline-offset: -2px;
          }
          
          .sort-icon {
            margin-left: 4px;
            font-size: 13px;
            font-weight: bold;
          }
          
          a {
            color: var(--primary-color, #03a9f4);
            text-decoration: none;
          }
          a:hover { text-decoration: underline; }
          a:focus-visible {
            outline: 2px solid var(--primary-color, #03a9f4);
            outline-offset: 2px;
          }
          
          /* Severity Colors — Story 2-3: Ratio-Based Severity */
          /* Critical (ratio 0-33): red color */
          .severity-critical { color: #F44336; font-weight: 500; }
          .severity-critical ha-icon { color: #F44336; }
          /* Warning (ratio 34-66): orange color */
          .severity-warning { color: #FF9800; font-weight: 500; }
          .severity-warning ha-icon { color: #FF9800; }
          /* Notice (ratio 67-100): yellow color */
          .severity-notice { color: #FFEB3B; font-weight: 500; }
          .severity-notice ha-icon { color: #FFEB3B; }
          
          /* Legacy severity colors for backward compatibility */
          .severity-red { color: #F44336; font-weight: 500; }
          .severity-red ha-icon { color: #F44336; }
          .severity-orange { color: #FF9800; font-weight: 500; }
          .severity-orange ha-icon { color: #FF9800; }
          .severity-yellow { color: #FFEB3B; font-weight: 500; }
          .severity-yellow ha-icon { color: #FFEB3B; }
          
          .loading {
            text-align: center;
            padding: 24px;
            color: var(--secondary-text-color, #888);
            font-size: 14px;
          }
          .end-message {
            text-align: center;
            padding: 8px;
            color: var(--secondary-text-color, #888);
            font-size: 12px;
          }
          
          /* Responsive Design — Tablet (768px) */
          @media (max-width: 768px) {
            th[data-col="area"],
            th[data-col="manufacturer"],
            td.hidden-tablet {
              display: none;
            }
          }
          
          /* Responsive Design — Mobile (375px) */
          @media (max-width: 375px) {
            :host { padding: 12px; }
            table { font-size: 12px; }
            th, td { padding: 6px 8px; }
            th[data-col="area"],
            th[data-col="manufacturer"],
            th[data-col="model"],
            th[data-col="updated_at"],
            td.hidden-mobile {
              display: none;
            }
            .sort-icon { font-size: 11px; }
          }
          
          /* Reduced Motion Support */
          @media (prefers-reduced-motion: reduce) {
            * { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; }
          }
          
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

      // Build table headers with ARIA attributes
      const headerRow = cols
        .map((col) => {
          const isActive = sort.by === col.key;
          const ariaSort = isActive ? (sort.dir === "asc" ? "ascending" : "descending") : "none";
          const icon = isActive ? (sort.dir === "asc" ? "▲" : "▼") : "";
          const sortLabel = isActive ? `${col.label}, currently sorted ${sort.dir === "asc" ? "ascending" : "descending"}` : `Sort by ${col.label}`;
          return `<th data-col="${col.key}" aria-sort="${ariaSort}" role="columnheader" tabindex="0" aria-label="${this._esc(sortLabel)}">${col.label}<span class="sort-icon" aria-hidden="true">${icon}</span></th>`;
        })
        .join("");

      const bodyRows = rows
        .map((row) => {
          const cells = cols.map((col) => {
            const isMobileHidden = ["area", "manufacturer", "model", "updated_at"].includes(col.key);
            const mobileClass = isMobileHidden ? "hidden-mobile" : "";
            const isTabletHidden = ["manufacturer"].includes(col.key);
            const tabletClass = isTabletHidden ? "hidden-tablet" : "";
            const className = `${mobileClass} ${tabletClass}`.trim();

            if (col.key === "friendly_name") {
              const href = `/config/entities/entity/${row.entity_id}`;
              return `<td class="${className}"><a href="${href}" target="_blank">${this._esc(row.friendly_name || row.entity_id)}</a></td>`;
            }
            if (col.key === "battery_level") {
              const sevClass = row.severity ? `severity-${row.severity}` : "";
              const icon = row.severity_icon ? `<ha-icon icon="${this._esc(row.severity_icon)}"></ha-icon> ` : "";
              return `<td class="${sevClass} ${className}">${icon}${this._esc(row.battery_display || "")}</td>`;
            }
            if (col.key === "updated_at" && row.updated_at) {
              return `<td class="${className}">${new Date(row.updated_at).toLocaleString()}</td>`;
            }
            return `<td class="${className}">${this._esc(row[col.key] || "")}</td>`;
          });
          return `<tr>${cells.join("")}</tr>`;
        })
        .join("");

      const tableLabel = tab === TAB_LOW_BATTERY 
        ? "Low battery entities table, sortable" 
        : "Unavailable entities table, sortable";

      container.innerHTML = `
        <table aria-label="${this._esc(tableLabel)}" role="grid">
          <thead><tr>${headerRow}</tr></thead>
          <tbody>${bodyRows}</tbody>
        </table>
        ${this._loading ? '<div class="loading" role="status" aria-live="polite" aria-atomic="true">Loading…</div>' : ""}
        ${this._end[tab] && rows.length > 0 ? '<div class="end-message" role="status" aria-live="polite">All entities loaded</div>' : ""}
      `;

      // Attach sort click handlers to table headers
      container.querySelectorAll("th[data-col]").forEach((th) => {
        th.addEventListener("click", () => this._onSortClick(th.dataset.col));
        // Allow keyboard navigation (Enter/Space)
        th.addEventListener("keydown", (e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            this._onSortClick(th.dataset.col);
          }
        });
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
      try {
        localStorage.setItem(STORAGE_KEY, tab);
      } catch (e) {
        // Private browsing mode or localStorage unavailable - silently fail
      }
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
