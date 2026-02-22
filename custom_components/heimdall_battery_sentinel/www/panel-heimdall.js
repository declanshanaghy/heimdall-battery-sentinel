/**
 * Heimdall Battery Sentinel - Frontend Panel
 * Plain JavaScript module for Home Assistant custom panel
 */

class HeimdallPanel {
  constructor() {
    this.hass = null;
    this.connected = false;
    this.activeTab = 'low_battery';
    this.data = {
      low_battery: [],
      unavailable: []
    };
    this.counts = { low_battery: 0, unavailable: 0 };
    this.sortBy = 'friendly_name';
    this.sortDir = 'asc';
    this.pages = { low_battery: 0, unavailable: 0 };
    this.loading = false;
    this.endReached = { low_battery: false, unavailable: false };
    this.datasetVersion = { low_battery: 0, unavailable: 0 };
    this.subscriptionId = null;
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
          margin-bottom: 16px;
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
      </style>
      <div class="header">
        <h1>Heimdall Battery Sentinel</h1>
      </div>
      <div class="tabs">
        <button class="tab active" data-tab="low_battery">
          Low Battery <span class="count" id="low-battery-count">0</span>
        </button>
        <button class="tab" data-tab="unavailable">
          Unavailable <span class="count" id="unavailable-count">0</span>
        </button>
      </div>
      <div id="content"></div>
    `;

    this._attachListeners();
    await this._connect();
  }

  _attachListeners() {
    this.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const tabName = e.target.dataset.tab;
        this.setActiveTab(tabName);
      });
    });
  }

  async setActiveTab(tab) {
    this.activeTab = tab;
    this.querySelectorAll('.tab').forEach(t => {
      t.classList.toggle('active', t.dataset.tab === tab);
    });
    
    if (this.data[tab].length === 0 && !this.endReached[tab]) {
      await this._loadPage(tab);
    } else {
      this._render();
    }
  }

  async _connect() {
    this.hass = window.hass;
    await this._fetchSummary();
    await this._subscribe();
    this._render();
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
    }
    
    this.loading = false;
    this._render();
  }

  _updateCounts() {
    this.querySelector('#low-battery-count').textContent = this.counts.low_battery;
    this.querySelector('#unavailable-count').textContent = this.counts.unavailable;
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
      <table>
        <thead>
          <tr>
            <th data-sort="friendly_name">Name<span class="sort-icon ${this.sortBy === 'friendly_name' ? 'active' : ''}">${this.sortBy === 'friendly_name' ? (this.sortDir === 'asc' ? '↑' : '↓') : ''}</span></th>
            <th data-sort="area">Area<span class="sort-icon ${this.sortBy === 'area' ? 'active' : ''}">${this.sortBy === 'area' ? (this.sortDir === 'asc' ? '↑' : '↓') : ''}</span></th>
            ${tab === 'low_battery' ? '<th data-sort="battery_level">Battery<span class="sort-icon ${this.sortBy === \'battery_level\' ? \'active\' : \'\'}">' + (this.sortBy === 'battery_level' ? (this.sortDir === 'asc' ? '↑' : '↓') : '') + '</span></th>' : ''}
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
      html += `
        <tr>
          <td>${row.friendly_name || row.entity_id}</td>
          <td>${displayArea}</td>
          ${tab === 'low_battery' ? `<td class="${severityClass}">${iconHtml}${row.battery_display}</td>` : ''}
          <td>${displayManufacturer}</td>
          <td>${displayModel}</td>
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
    });
    
    // Infinite scroll
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && !this.loading && !this.endReached[tab]) {
        this._loadPage(tab);
      }
    }, { rootMargin: '100px' });
    
    const loadingMore = content.querySelector('#loading-more');
    if (loadingMore) {
      observer.observe(loadingMore);
    }
  }
}

customElements.define('heimdall-panel', HeimdallPanel);
