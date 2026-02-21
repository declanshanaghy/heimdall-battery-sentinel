#!/bin/bash
# Deploy script for heimdall-battery-sentinel to Home Assistant
# Usage: ./deploy.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$REPO_ROOT/.env"

# Load credentials from .env
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

HA_URL="${HOME_ASSISTANT_URL:-http://homeassistant.lan:8123}"
HA_TOKEN="$HOME_ASSISTANT_TOKEN"
HA_HOST="${HOME_ASSISTANT_HOST:-homeassistant}"
HA_PORT="${HOME_ASSISTANT_PORT:-2222}"
HA_USER="${HOME_ASSISTANT_SSH_USER:-root}"
HA_PATH="${HOME_ASSISTANT_CONFIG_PATH:-/root/homeassistant}"

INTEGRATION_NAME="heimdall_battery_sentinel"
INTEGRATION_PATH="custom_components/$INTEGRATION_NAME"

# Strip quotes if present
HA_TOKEN="${HA_TOKEN//\"/}"

echo "=== Heimdall Battery Sentinel Deployment ==="
echo "HA Host: $HA_HOST:$HA_PORT"
echo "HA Config Path: $HA_PATH"
echo "HA URL: $HA_URL"
echo ""

# Function to check if integration is installed
check_integration() {
    result=$(curl -s -X GET "$HA_URL/api/config_entries" \
        -H "Authorization: Bearer $HA_TOKEN" \
        -H "Content-Type: application/json")
    
    if echo "$result" | grep -q "$INTEGRATION_NAME"; then
        return 0  # installed
    else
        return 1  # not installed
    fi
}

# Function to get config entry ID
get_config_entry_id() {
    result=$(curl -s -X GET "$HA_URL/api/config_entries" \
        -H "Authorization: Bearer $HA_TOKEN" \
        -H "Content-Type: application/json")
    
    entry_id=$(echo "$result" | python3 -c "
import sys, json
entries = json.load(sys.stdin)
for entry in entries:
    if 'heimdall' in entry.get('domain', ''):
        print(entry.get('entry_id', ''))
" 2>/dev/null)
    
    echo "$entry_id"
}

# Function to uninstall integration
uninstall_integration() {
    local entry_id="$1"
    
    if [ -n "$entry_id" ]; then
        echo "Uninstalling integration (entry_id: $entry_id)..."
        curl -s -X DELETE "$HA_URL/api/config_entries/entry/$entry_id" \
            -H "Authorization: Bearer $HA_TOKEN" \
            -H "Content-Type: application/json"
        echo "Integration uninstalled."
    else
        echo "Integration not installed, skipping uninstall."
    fi
}

# Copy integration files via SCP
copy_integration_files() {
    echo "Copying integration files to HA server..."
    
    local remote_path="$HA_PATH/custom_components"
    
    # Create remote directory (disable host key checking for first connect)
    ssh -o StrictHostKeyChecking=no -p $HA_PORT $HA_USER@$HA_HOST "mkdir -p $remote_path"
    
    # Remove old integration if exists
    ssh -o StrictHostKeyChecking=no -p $HA_PORT $HA_USER@$HA_HOST "rm -rf $remote_path/$INTEGRATION_NAME"
    
    # Copy new integration
    scp -o StrictHostKeyChecking=no -P $HA_PORT -r "$REPO_ROOT/$INTEGRATION_PATH" "$HA_USER@$HA_HOST:$remote_path/"
    
    echo "Integration files copied."
}

# Function to reload custom components
reload_custom_components() {
    echo "Reloading custom components..."
    curl -s -X POST "$HA_URL/api/services/homeassistant/reload_custom_components" \
        -H "Authorization: Bearer $HA_TOKEN" \
        -H "Content-Type: application/json"
    echo "Custom components reloaded."
}

# Function to restart Home Assistant
restart_ha() {
    echo "Restarting Home Assistant..."
    curl -s -X POST "$HA_URL/api/services/homeassistant/restart" \
        -H "Authorization: Bearer $HA_TOKEN" \
        -H "Content-Type: application/json"
    
    echo "Home Assistant restart requested."
    echo "Waiting for HA to come back online..."
    
    # Wait for HA to be ready
    for i in {1..60}; do
        status=$(curl -s -o /dev/null -w "%{http_code}" "$HA_URL/api/" -H "Authorization: Bearer $HA_TOKEN" 2>/dev/null)
        if [ "$status" = "200" ]; then
            echo "Home Assistant is online!"
            return 0
        fi
        sleep 2
    done
    
    echo "Warning: Could not confirm HA is back online, but restart was requested."
    return 1
}

# Main execution
echo "Step 1: Validating authentication..."
auth_test=$(curl -s -o /dev/null -w "%{http_code}" "$HA_URL/api/" -H "Authorization: Bearer $HA_TOKEN")
if [ "$auth_test" != "200" ]; then
    echo "Error: Authentication failed (HTTP $auth_test)"
    exit 1
fi
echo "Authenticated successfully."

echo ""
echo "Step 2: Checking integration status..."
if check_integration; then
    echo "Integration is installed."
    ENTRY_ID=$(get_config_entry_id)
else
    echo "Integration is not installed."
    ENTRY_ID=""
fi

echo ""
echo "Step 3: Uninstalling old integration..."
uninstall_integration "$ENTRY_ID"

echo ""
echo "Step 4: Copying integration files to HA server..."
copy_integration_files

echo ""
echo "Step 5: Restarting Home Assistant..."
restart_ha

echo ""
echo "=== Deployment Complete! ==="
echo "The integration should now be available in Home Assistant."
echo "Go to Configuration > Integrations to configure it."
