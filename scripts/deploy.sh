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

HA_URL="${DEV_SERVER_URL:-http://homeassistant.lan:8123}"
HA_USER="$HOME_ASSISTANT_USERNAME"
HA_PASS="$HOME_ASSISTANT_PASSWORD"
INTEGRATION_NAME="heimdall_battery_sentinel"
INTEGRATION_PATH="custom_components/$INTEGRATION_NAME"

echo "=== Heimdall Battery Sentinel Deployment ==="
echo "HA URL: $HA_URL"
echo "User: $HA_USER"
echo ""

# Function to get auth token
get_auth_token() {
    response=$(curl -s -X POST "$HA_URL/api/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\": \"$HA_USER\", \"password\": \"$HA_PASS\"}")
    
    token=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('token', ''))" 2>/dev/null)
    
    if [ -z "$token" ]; then
        echo "Error: Failed to get auth token"
        echo "Response: $response"
        exit 1
    fi
    
    echo "$token"
}

# Function to check if integration is installed
check_integration() {
    local token="$1"
    result=$(curl -s -X GET "$HA_URL/api/config_entries" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json")
    
    if echo "$result" | grep -q "$INTEGRATION_NAME"; then
        return 0  # installed
    else
        return 1  # not installed
    fi
}

# Function to get config entry ID
get_config_entry_id() {
    local token="$1"
    result=$(curl -s -X GET "$HA_URL/api/config_entries" \
        -H "Authorization: Bearer $token" \
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
    local token="$1"
    local entry_id="$2"
    
    if [ -n "$entry_id" ]; then
        echo "Uninstalling integration (entry_id: $entry_id)..."
        curl -s -X DELETE "$HA_URL/api/config_entries entry/$entry_id" \
            -H "Authorization: Bearer $token" \
            -H "Content-Type: application/json"
        echo "Integration uninstalled."
    else
        echo "Integration not installed, skipping uninstall."
    fi
}

# Function to install integration
install_integration() {
    echo "Installing integration..."
    
    # Create custom_components directory if it doesn't exist
    HA_CONFIG_DIR="$HA_CONFIG_DIR"
    if [ -z "$HA_CONFIG_DIR" ]; then
        # Try default locations
        if [ -d "$HOME/.homeassistant" ]; then
            HA_CONFIG_DIR="$HOME/.homeassistant"
        elif [ -d "$HOME/config" ]; then
            HA_CONFIG_DIR="$HOME/config"
        else
            echo "Error: Could not find Home Assistant config directory"
            exit 1
        fi
    fi
    
    CUSTOM_COMPONENTS="$HA_CONFIG_DIR/custom_components"
    
    # Create directory
    mkdir -p "$CUSTOM_COMPONENTS"
    
    # Remove old installation if exists
    if [ -d "$CUSTOM_COMPONENTS/$INTEGRATION_NAME" ]; then
        echo "Removing old installation..."
        rm -rf "$CUSTOM_COMPONENTS/$INTEGRATION_NAME"
    fi
    
    # Copy new integration
    echo "Copying integration to $CUSTOM_COMPONENTS..."
    cp -r "$REPO_ROOT/$INTEGRATION_PATH" "$CUSTOM_COMPONENTS/"
    
    echo "Integration installed."
}

# Function to restart Home Assistant
restart_ha() {
    local token="$1"
    
    echo "Restarting Home Assistant..."
    curl -s -X POST "$HA_URL/api/services/homeassistant/restart" \
        -H "Authorization: Bearer $token" \
        -H "Content-Type: application/json"
    
    echo "Home Assistant restart requested."
    echo "Waiting for HA to come back online..."
    
    # Wait for HA to be ready
    for i in {1..30}; do
        if curl -s -o /dev/null -w "%{http_code}" "$HA_URL/api/" | grep -q "200"; then
            echo "Home Assistant is online!"
            return 0
        fi
        sleep 2
    done
    
    echo "Warning: Could not confirm HA is back online, but restart was requested."
    return 1
}

# Main execution
echo "Step 1: Getting authentication..."
TOKEN=$(get_auth_token)
echo "Authenticated successfully."

echo ""
echo "Step 2: Checking integration status..."
if check_integration "$TOKEN"; then
    echo "Integration is installed."
    ENTRY_ID=$(get_config_entry_id "$TOKEN")
else
    echo "Integration is not installed."
    ENTRY_ID=""
fi

echo ""
echo "Step 3: Uninstalling old integration..."
uninstall_integration "$TOKEN" "$ENTRY_ID"

echo ""
echo "Step 4: Installing new integration..."
install_integration

echo ""
echo "Step 5: Restarting Home Assistant..."
restart_ha "$TOKEN"

echo ""
echo "=== Deployment Complete! ==="
echo "The integration should now be available in Home Assistant."
echo "Go to Configuration > Integrations to configure it."
