# Heimdall Battery Sentinel

A Home Assistant integration that displays low battery and unavailable entities in a dedicated sidebar page with live updates via WebSocket.

## Features

- **Low Battery Tracking**: Displays all entities with battery state below a configurable threshold (numeric % or textual "low")
- **Unavailable Entity Detection**: Shows all entities that are currently unavailable
- **Live Updates**: Real-time updates via WebSocket - no polling required
- **Server-side Sorting & Paging**: Sort by friendly name, area, or battery level with infinite scroll support
- **Metadata Enrichment**: Shows manufacturer, model, and area for each entity

## Installation

### Option 1: HACS (Recommended)

1. Open Home Assistant
2. Go to HACS > Integrations
3. Click the three dots (top right) > Custom repositories
4. Add: `https://github.com/declanshanaghy/heimdall-battery-sentinel`
5. Category: Integration
6. Click Add
7. Find "Heimdall Battery Sentinel" and install

### Option 2: Manual

1. Copy the `custom_components/heimdall_battery_sentinel` folder to your Home Assistant's `custom_components` folder
2. Restart Home Assistant
3. Go to Settings > Devices & Services > Add Integration
4. Search for "Heimdall Battery Sentinel"

## Configuration

After installation, the integration can be configured via the UI:

1. Go to Settings > Devices & Services
2. Click Add Integration
3. Search for "Heimdall Battery Sentinel"
4. Configure the low battery threshold (5-100%, default: 15%)

## Usage

After configuration, a new sidebar page called "Battery Sentinel" will appear in your Home Assistant sidebar. It shows two tabs:

- **Low Battery**: Entities with battery level below the configured threshold
- **Unavailable**: All entities that are currently unavailable

Both tables support:
- Sorting by name, area, or battery level (click column headers)
- Infinite scroll for large datasets (100 rows per page)
- Click on entity name to open entity details in HA

## Battery Detection Rules

- **Numeric batteries**: Only entities with `unit_of_measurement: "%"` are included
- **Textual batteries**: Only state `low` is included (medium and high are excluded)
- **Threshold**: Configurable from 5-100% (numeric batteries only)

## Requirements

- Home Assistant 2024.11.0 or later
- HACS (for HACS installation method)

## Support

- Report issues: https://github.com/declanshanaghy/heimdall-battery-sentinel/issues
- Feature requests: https://github.com/declanshanaghy/heimdall-battery-sentinel/discussions

## License

MIT License