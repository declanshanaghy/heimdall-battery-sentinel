/**
 * Heimdall Battery Sentinel - Frontend Panel
 * Plain JavaScript module for Home Assistant custom panel
 */

const TAB_STORAGE_KEY = 'heimdall-tab';

class HeimdallPanel {
  constructor() {
    this.hass = null;
    this.connected = false;
    this.activeTab = this._loadTabFromStorage();
    this.data = {
      low_battery: [],
      unavailable: []
    };
    this.counts = { low_battery: 0, unavailable: 0 };
    this.sortBy = 'friendly_name';
    this.sortDir = 'asc';
    this.sortableColumns = ['friendly_name', 'area', 'battery_level', 'updated_at'];
    this.pages = { low_battery: 0, unavailable: 0 };
    this.loading = false;
    this.endReached = { low_battery: false, unavailable: false };
    this.datasetVersion = { low_battery: 0, unavailable: 0 };
    this.subscriptionId = null;
  }

  _loadTabFromStorage() {
    try {
      const saved = localStorage.getItem(TAB_STORAGE_KEY);
      if (saved === 'low_battery' || saved === 'unavailable') {
        return saved;
      }
    } catch (e) {
      // localStorage not available
    }
    return 'low_battery';
  }

  _saveTabToStorage(tab) {
    try {
      localStorage.setItem(TAB_STORAGE_KEY, tab);
    } catch (e) {
      // localStorage not available
    }
  }

  async connectedCallback() {
    this.innerHTML = `
      <style>
        :host {
          display: block;
          padding: 16px;
          font-family: var(--ha-font-family);
        }
        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 16px;
          flex-wrap: wrap;
          gap: 12px;
        }
        .header h1 {
          margin: 0;
          font-size: 24px;
          font-weight: 400;
        }
        .tabs {
          display: flex;
          gap: 8px;
          margin-bottom: 16px;
        }
        .tab {
          padding: 8px 16px;
          border: none;
          background: var(--ha-card-background, #fff);
          cursor: pointer;
          border-radius: 4px;
          font-size: 14px;
          transition: background-color 0.2s, color 0.2s;
        }
        .tab:hover {
          background: var(--hover-color, #f0f0f0);
        }
        .tab:focus {
          outline: 2px solid var(--primary-color, #03a9f4);
          outline-offset: 2px;
        }
        .tab.active {
          background: var(--primary-color, #03a9f4);
          color: white;
        }
        .count {
          background: var(--secondary-text-color, #666);
          color: white;
          padding: 2px 6px;
          border-radius: 10px;
          font-size: 12px;
          margin-left: 4px;
        }
        table {
          width: 100%;
          border-collapse: collapse;
        }
        th, td {
          text-align: left;
          padding: 12px 8px;
          border-bottom: 1px solid var(--divider-color, #e0e0e0);
        }
        th {
          cursor: pointer;
          font-weight: 500;
        }
        th:hover {
          background: var(--hover-color, #f5f5f5);
        }
        th:focus {
          outline: 2px solid var(--primary-color, #03a9f4);
          outline-offset: -2px;
        }
        .sort-icon {
          margin-left: 4px;
          opacity: 0.5;
        }
        .sort-icon.active {
          opacity: 1;
        }
        .loading {
          text-align: center;
          padding: 20px;
          color: var(--secondary-text-color, #666);
        }
        .end-message {
          text-align: center;
          padding: 20px;
          color: var(--secondary-text-color, #666);
        }
        .error-message {
          background: #ffebee;
          color: #c62828;
          padding: 12px 16px;
          border-radius: 4px;
          margin-bottom: 16px;
          border-left: 4px solid #c62828;
        }
        .severity-yellow { color: #fdd835; }
        .severity-orange { color: #ff9800; }
        .severity-red { color: #f44336; }
        .severity-icon {
          margin-right: 4px;
          vertical-align: middle;
        }
        .empty-state {
          text-align: center;
          padding: 40px;
          color: var(--secondary-text-color, #666);
        }
        .footer {
          margin-top: 24px;
          padding: 16px;
          background: var(--ha-card-background, #fff);
          border-radius: 8px;
          display: flex;
          align-items: center;
          gap: 16px;
          flex-wrap: wrap;
        }
        .threshold-label {
          font-size: 14px;
          color: var(--secondary-text-color, #666);
        }
        .threshold-slider {
          flex: 1;
          min-width: 150px;
        }
        .threshold-value {
          font-weight: 500;
          min-width: 40px;
        }
        
        /* Responsive styles */
        @media (max-width: 768px) {
          :host {
            padding: 12px;
          }
          .header h1 {
            font-size: 20px;
          }
          .tabs {
            width: 100%;
          }
          .tab {
            flex: 1;
            text-align: center;
            padding: 10px 8px;
          }
          table, thead, tbody, th, td, tr {
            display: block;
          }
          thead tr {
            position: absolute;
            top: -9999px;
            left: -9999px;
          }
          tr {
            margin-bottom: 12px;
            border: 1px solid var(--divider-color, #e0e0e0);
            border-radius: 4px;
            overflow: hidden;
          }
          td {
            border: none;
            position: relative;
            padding-left: 50%;
            border-bottom: 1px solid var(--divider-color, #e0e0e0);
          }
          td:last-child {
            border-bottom: none;
          }
          td:before {
            position: absolute;
            top: 12px;
            left: 8px;
            width: 45%;
            padding-right: 10px;
            white-space: nowrap;
            font-weight: 500;
            content: attr(data-label);
          }
        }
        
        @media (max-width: 480px) {
          :host {
            padding: 8px;
          }
          .header {
            flex-direction: column;
            align-items: flex-start;
          }
          .footer {
            flex-direction: column;
            align-items: flex-start;
          }
          .threshold-slider {
            width: 100%;
          }
        }
      </style>
      <div class="header">
        <h1>Heimdall Battery Sentinel</h1>
      </div>
      <div class="tabs" role="tablist" aria-label="Battery monitoring tabs">
        <button class="tab active" data-tab="low_battery" role="tab" aria-selected="true" aria-controls="content" id="tab-low_battery" tabindex="0">
          Low Battery <span class="count" id="low-battery-count">0</span>
        </button>
        <button class="tab" data-tab="unavailable" role="tab" aria-selected="false" aria-controls="content" id="tab-unavailable" tabindex="-1">
          Unavailable <span class="count" id="unavailable-count">0</span>
        </button>
      </div>
      <div id="content" role="tabpanel" aria-labelledby="tab-low_battery"></div>
      <div class="footer">
        <span class="threshold-label">Battery threshold:</span>
        <input type="range" class="threshold-slider" min="0" max="100" value="20" aria-label="Battery threshold percentage" />
        <span class="threshold-value">20%</span>
        <span class="threshold-label">(Coming soon)</span>
      </div>
    `;

    this._attachListeners();
    this._updateTabUI();
    await this._connect();
  }

  _updateTabUI() {
    // Set initial active tab in UI from storage
    this.querySelectorAll('.tab').forEach(t => {
      const isActive = t.dataset.tab === this.activeTab;
      t.classList.toggle('active', isActive);
      t.setAttribute('aria-selected', isActive);
      t.setAttribute('tabindex', isActive ? '0' : '-1');
    });
  }

  _attachListeners() {
    // Tab click handlers
    this.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const tabName = e.target.dataset.tab;
        this.setActiveTab(tabName);
      });
    });
    
    // Keyboard navigation for tabs
    this.querySelector('.tabs').addEventListener('keydown', (e) => {
      const tabs = Array.from(this.querySelectorAll('.tab'));
      const currentIndex = tabs.findIndex(t => t === document.activeElement);
      
      if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
        e.preventDefault();
        const direction = e.key === 'ArrowRight' ? 1 : -1;
        const nextIndex = (currentIndex + direction + tabs.length) % tabs.length;
        tabs[nextIndex].focus();
        tabs[nextIndex].click();
      }
    });
  }

  async setActiveTab(tab) {
    this.activeTab = tab;
    this._saveTabToStorage(tab);
    this.querySelectorAll('.tab').forEach(t => {
      const isActive = t.dataset.tab === tab;
      t.classList.toggle('active', isActive);
      t.setAttribute('aria-selected', isActive);
      t.setAttribute('tabindex', isActive ? '0' : '-1');
    });
    
    // Update tabpanel label
    this.querySelector('#content').setAttribute('aria-labelledby', `tab-${tab}`);
    
    if (this.data[tab].length === 0 && !this.endReached[tab]) {
      await this._loadPage(tab);
    } else {
      this._render();
    }
  }

  async _connect() {
    this.hass = window.hass;
    
    // Listen for subscription events from backend
    this.hass.connection.addEventListener('message', (event) => {
      const msg = event.data;
      this._handleSubscriptionMessage(msg);
    });
    
    await this._fetchSummary();
    await this._subscribe();
    this._render();
  }

  _handleSubscriptionMessage(msg) {
    // Handle subscription event messages
    // These are pushed from the store when data changes
    if (!msg || msg.type !== 'event') return;
    
    const event = msg.event || msg;
    const eventType = event.type;
    
    // Handle summary updates (count changes)
    if (eventType === 'summary' || eventType === 'upsert' || eventType === 'remove' || eventType === 'invalidated') {
      // Fetch updated counts when any data changes
      this._fetchSummary();
    }
  }

  async _fetchSummary() {
    try {
      const result = await this.hass.connection.sendMessage({
        id: Date.now(),
        type: 'heimdall/summary'
      });
      
      if (result && result.result) {
        this.counts.low_battery = result.result.low_battery_count;
        this.counts.unavailable = result.result.unavailable_count;
        this._updateCounts();
      }
    } catch (err) {
      console.error('Failed to fetch summary:', err);
    }
  }

  async _subscribe() {
    try {
      const result = await this.hass.connection.sendMessage({
        id: Date.now(),
        type: 'heimdall/subscribe'
      });
      
      this.subscriptionId = result.id;
    } catch (err) {
      console.error('Failed to subscribe:', err);
    }
  }

  async _loadPage(tab) {
    if (this.loading || this.endReached[tab]) return;
    
    this.loading = true;
    this._render();
    
    try {
      const offset = this.data[tab].length;
      const result = await this.hass.connection.sendMessage({
        id: Date.now(),
        type: 'heimdall/list',
        data: {
          tab: tab,
          offset: offset,
          page_size: 100,
          sort_by: this.sortBy,
          sort_dir: this.sortDir,
          dataset_version: this.datasetVersion[tab]
        }
      });
      
      if (result && result.result) {
        const { rows, end, dataset_version, invalidated } = result.result;
        
        if (invalidated) {
          this.data[tab] = [];
          this.datasetVersion[tab] = dataset_version;
        }
        
        this.data[tab] = [...this.data[tab], ...rows];
        this.endReached[tab] = end;
        this.datasetVersion[tab] = dataset_version;
      }
    } catch (err) {
      console.error('Failed to load page:', err);
      // Show user-visible error message (AC #4)
      this._showError('Failed to load more records. Please try again.');
    }
    
    this.loading = false;
    this._render();
  }

  _updateCounts() {
    this.querySelector('#low-battery-count').textContent = this.counts.low_battery;
    this.querySelector('#unavailable-count').textContent = this.counts.unavailable;
  }

  _showError(message) {
    // Create error toast/banner for user-visible error (AC #4)
    const content = this.querySelector('#content');
    const existingError = content.querySelector('.error-message');
    if (existingError) {
      existingError.remove();
    }
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.setAttribute('role', 'alert');
    errorDiv.textContent = message;
    
    // Insert at the top of content
    if (content.firstChild) {
      content.insertBefore(errorDiv, content.firstChild);
    } else {
      content.appendChild(errorDiv);
    }
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (errorDiv.parentNode) {
        errorDiv.remove();
      }
    }, 5000);
  }

  _render() {
    const content = this.querySelector('#content');
    const tab = this.activeTab;
    const rows = this.data[tab];
    
    if (this.loading && rows.length === 0) {
      content.innerHTML = '<div class="loading">Loading...</div>';
      return;
    }
    
    if (rows.length === 0) {
      content.innerHTML = `<div class="empty-state">No ${tab === 'low_battery' ? 'low battery' : 'unavailable'} entities</div>`;
      return;
    }
    
    let html = `
      <table role="grid">
        <thead>
          <tr>
            <th data-sort="friendly_name" tabindex="0">Name<span class="sort-icon ${this.sortBy === 'friendly_name' ? 'active' : ''}">${this.sortBy === 'friendly_name' ? (this.sortDir === 'asc' ? '↑' : '↓') : ''}</span></th>
            <th data-sort="area" tabindex="0">Area<span class="sort-icon ${this.sortBy === 'area' ? 'active' : ''}">${this.sortBy === 'area' ? (this.sortDir === 'asc' ? '↑' : '↓') : ''}</span></th>
            ${tab === 'low_battery' ? '<th data-sort="battery_level" tabindex="0">Battery<span class="sort-icon ${this.sortBy === \'battery_level\' ? \'active\' : \'\'}">' + (this.sortBy === 'battery_level' ? (this.sortDir === 'asc' ? '↑' : '↓') : '') + '</span></th>' : ''}
            <th data-sort="updated_at" tabindex="0">Last Checked<span class="sort-icon ${this.sortBy === 'updated_at' ? 'active' : ''}">${this.sortBy === 'updated_at' ? (this.sortDir === 'asc' ? '↑' : '↓') : ''}</span></th>
            <th>Manufacturer</th>
            <th>Model</th>
          </tr>
        </thead>
        <tbody>
    `;
    
    rows.forEach(row => {
      const severityClass = row.severity ? `severity-${row.severity}` : '';
      const severityIcon = row.severity === 'red' ? 'mdi:battery-alert' 
                        : row.severity === 'orange' ? 'mdi:battery-low'
                        : row.severity === 'yellow' ? 'mdi:battery-medium'
                        : '';
      const iconHtml = severityIcon ? `<ha-icon class="severity-icon" icon="${severityIcon}"></ha-icon>` : '';
      const displayArea = row.area || 'Unassigned';
      const displayManufacturer = row.manufacturer || 'Unknown';
      const displayModel = row.model || 'Unknown';
      
      // Format the updated_at date
      let displayLastChecked = 'Unknown';
      if (row.updated_at) {
        try {
          const date = new Date(row.updated_at);
          if (!isNaN(date.getTime())) {
            displayLastChecked = date.toLocaleString();
          }
        } catch (e) {
          displayLastChecked = row.updated_at;
        }
      }
      
      html += `
        <tr>
          <td data-label="Name">${row.friendly_name || row.entity_id}</td>
          <td data-label="Area">${displayArea}</td>
          ${tab === 'low_battery' ? `<td data-label="Battery" class="${severityClass}">${iconHtml}${row.battery_display}</td>` : ''}
          <td data-label="Last Checked">${displayLastChecked}</td>
          <td data-label="Manufacturer">${displayManufacturer}</td>
          <td data-label="Model">${displayModel}</td>
        </tr>
      `;
    });
    
    html += '</tbody></table>';
    
    if (!this.endReached[tab]) {
      html += '<div class="loading" id="loading-more">Loading more...</div>';
    } else if (rows.length > 0) {
      html += '<div class="end-message">End of list</div>';
    }
    
    content.innerHTML = html;
    
    // Attach sort handlers
    content.querySelectorAll('th[data-sort]').forEach(th => {
      th.addEventListener('click', () => {
        const sortKey = th.dataset.sort;
        if (this.sortBy === sortKey) {
          this.sortDir = this.sortDir === 'asc' ? 'desc' : 'asc';
        } else {
          this.sortBy = sortKey;
          this.sortDir = 'asc';
        }
        // Reset and reload
        this.data[tab] = [];
        this.endReached[tab] = false;
        this._loadPage(tab);
      });
      
      // Keyboard sort
      th.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          th.click();
        }
      });
    });
    
    // Infinite scroll - 200px threshold per AC #1
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && !this.loading && !this.endReached[tab]) {
        this._loadPage(tab);
      }
    }, { rootMargin: '200px' });
    
    const loadingMore = content.querySelector('#loading-more');
    if (loadingMore) {
      observer.observe(loadingMore);
    }
  }
}

customElements.define('heimdall-panel', HeimdallPanel);