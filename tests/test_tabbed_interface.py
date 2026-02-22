"""Tests for tab persistence in frontend panel."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
INTEGRATION_DIR = PROJECT_ROOT / "custom_components" / "heimdall_battery_sentinel"


class TestTabPersistence:
    """Test tab state persistence in frontend."""

    def test_localstorage_key_defined(self):
        """Verify localStorage key is defined for tab persistence."""
        panel_path = INTEGRATION_DIR / "www" / "panel-heimdall.js"
        assert panel_path.exists(), f"Panel file not found: {panel_path}"
        
        with open(panel_path) as f:
            content = f.read()
        
        # Check that localStorage key is used for tab persistence
        assert "localStorage" in content, "localStorage not used in panel"
        assert "heimdall-tab" in content, "Tab persistence key not found"

    def test_tab_state_restored_on_load(self):
        """Verify tab state is restored from localStorage on panel load."""
        panel_path = INTEGRATION_DIR / "www" / "panel-heimdall.js"
        
        with open(panel_path) as f:
            content = f.read()
        
        # Check that restore logic exists (reading from localStorage)
        assert "getItem" in content, "getItem not used to restore tab state"

    def test_tab_state_saved_on_switch(self):
        """Verify tab state is saved to localStorage when switching tabs."""
        panel_path = INTEGRATION_DIR / "www" / "panel-heimdall.js"
        
        with open(panel_path) as f:
            content = f.read()
        
        # Check that setItem is used when switching tabs
        assert "setItem" in content, "setItem not used to save tab state"


class TestLiveCounts:
    """Test live count updates in frontend."""

    def test_count_update_handler_exists(self):
        """Verify frontend handles count update events from subscription."""
        panel_path = INTEGRATION_DIR / "www" / "panel-heimdall.js"
        
        with open(panel_path) as f:
            content = f.read()
        
        # Check that subscription events are handled
        assert "addEventListener" in content or "message" in content, \
            "No event/message handling found for subscription updates"

    def test_summary_subscription_exists(self):
        """Verify frontend subscribes to summary updates."""
        panel_path = INTEGRATION_DIR / "www" / "panel-heimdall.js"
        
        with open(panel_path) as f:
            content = f.read()
        
        # The frontend should subscribe to updates
        assert "_subscribe" in content or "subscribe" in content, \
            "No subscription method found"
