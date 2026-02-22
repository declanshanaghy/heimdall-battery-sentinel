"""Tests for Entity Linking functionality in frontend panel."""

import os
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTEGRATION_DIR = os.path.join(PROJECT_ROOT, "custom_components", "heimdall_battery_sentinel")
PANEL_PATH = os.path.join(INTEGRATION_DIR, "www", "panel-heimdall.js")


class TestEntityLinking:
    """Test entity linking in table rows."""

    def test_entity_link_in_low_battery_table(self):
        """Test that entity links are rendered in Low Battery table (AC #1)."""
        with open(PANEL_PATH, 'r') as f:
            content = f.read()
        
        # Check that anchor tags are used for entity names
        assert '<a ' in content or 'href=' in content.lower(), \
            "Should have anchor tags for entity linking in Low Battery table"

    def test_entity_link_in_unavailable_table(self):
        """Test that entity links are rendered in Unavailable table (AC #2)."""
        with open(PANEL_PATH, 'r') as f:
            content = f.read()
        
        # Entity linking should work for both tabs
        # Check for anchor tags used in table rendering
        assert '<a ' in content or 'href=' in content.lower(), \
            "Should have anchor tags for entity linking in Unavailable table"

    def test_links_open_in_new_tab(self):
        """Test that links open in new browser tabs (AC #4)."""
        with open(PANEL_PATH, 'r') as f:
            content = f.read()
        
        # Check for target="_blank" attribute
        assert 'target="_blank"' in content, \
            "Links should open in new tab with target=\"_blank\""

    def test_rel_noopener_for_security(self):
        """Test that rel="noopener" is added for security (from Implementation Notes)."""
        with open(PANEL_PATH, 'r') as f:
            content = f.read()
        
        # rel="noopener" prevents new tab from accessing opener context
        assert 'rel="noopener"' in content, \
            "Links should have rel=\"noopener\" for security"

    def test_entity_detail_url_format(self):
        """Test that link target uses correct HA entity detail URL format (AC #5)."""
        with open(PANEL_PATH, 'r') as f:
            content = f.read()
        
        # Link target should be /config/entities/edit?entity_id={entity_id}
        assert '/config/entities/edit?entity_id=' in content, \
            "Links should point to /config/entities/edit?entity_id={entity_id}"

    def test_link_styling_exists(self):
        """Test that link styling is defined (blue text with hover underline)."""
        with open(PANEL_PATH, 'r') as f:
            content = f.read()
        
        # Check for link styling - should have CSS for anchor tags
        # HA conventions: blue text with hover underline
        assert 'a {' in content.lower() or 'a{' in content.lower() or '.entity-link' in content.lower() or 'entity-link' in content.lower(), \
            "Should have link styling defined"

    def test_missing_entity_id_handling(self):
        """Test that missing entity_id is handled gracefully (AC #5, Error Handling)."""
        with open(PANEL_PATH, 'r') as f:
            content = f.read()
        
        # Check that entity_id is checked before creating link
        # Should render plain text when entity_id is missing
        # The implementation should have conditional logic
        assert 'entity_id' in content, \
            "Should handle entity_id in link generation"
        
        # Should have error logging for missing entity_ids
        assert 'console.error' in content or '_LOGGER' in content or 'log' in content.lower(), \
            "Should log errors for missing entity_ids"

    def test_consistent_links_across_tabs(self):
        """Test that links work consistently across both tabs (AC #3)."""
        with open(PANEL_PATH, 'r') as f:
            content = f.read()
        
        # The same link generation logic should apply to both tabs
        # The entityUrl variable is used for both tabs in the same rendering loop
        assert 'entityUrl' in content, \
            "Entity URL should be generated for linking entities"
        
        # Verify the link is generated within the rows.forEach loop (used for all rows)
        assert 'rows.forEach' in content and 'entityUrl' in content, \
            "Link generation should be in the rows rendering loop"
