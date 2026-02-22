"""Tests for project structure setup."""

import json
import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
INTEGRATION_DIR = PROJECT_ROOT / "custom_components" / "heimdall_battery_sentinel"


class TestProjectStructure:
    """Test that the integration structure matches requirements."""

    def test_integration_directory_exists(self):
        """Verify integration directory exists."""
        assert INTEGRATION_DIR.exists(), f"Integration directory not found: {INTEGRATION_DIR}"
        assert INTEGRATION_DIR.is_dir(), f"Expected directory: {INTEGRATION_DIR}"

    def test_manifest_json_exists(self):
        """Verify manifest.json exists and is valid."""
        manifest_path = INTEGRATION_DIR / "manifest.json"
        assert manifest_path.exists(), f"manifest.json not found: {manifest_path}"
        
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        assert "domain" in manifest, "manifest.json missing 'domain'"
        assert manifest["domain"] == "heimdall_battery_sentinel", f"Wrong domain: {manifest['domain']}"
        assert "name" in manifest, "manifest.json missing 'name'"
        assert "version" in manifest, "manifest.json missing 'version'"

    def test_init_py_exists(self):
        """Verify __init__.py exists."""
        init_path = INTEGRATION_DIR / "__init__.py"
        assert init_path.exists(), f"__init__.py not found: {init_path}"

    def test_const_py_exists(self):
        """Verify const.py exists with domain constant."""
        const_path = INTEGRATION_DIR / "const.py"
        assert const_path.exists(), f"const.py not found: {const_path}"

    def test_config_flow_exists(self):
        """Verify config_flow.py exists."""
        config_flow_path = INTEGRATION_DIR / "config_flow.py"
        assert config_flow_path.exists(), f"config_flow.py not found: {config_flow_path}"

    def test_models_py_exists(self):
        """Verify models.py exists."""
        models_path = INTEGRATION_DIR / "models.py"
        assert models_path.exists(), f"models.py not found: {models_path}"

    def test_evaluator_py_exists(self):
        """Verify evaluator.py exists."""
        evaluator_path = INTEGRATION_DIR / "evaluator.py"
        assert evaluator_path.exists(), f"evaluator.py not found: {evaluator_path}"

    def test_registry_py_exists(self):
        """Verify registry.py exists."""
        registry_path = INTEGRATION_DIR / "registry.py"
        assert registry_path.exists(), f"registry.py not found: {registry_path}"

    def test_store_py_exists(self):
        """Verify store.py exists."""
        store_path = INTEGRATION_DIR / "store.py"
        assert store_path.exists(), f"store.py not found: {store_path}"

    def test_websocket_py_exists(self):
        """Verify websocket.py exists."""
        websocket_path = INTEGRATION_DIR / "websocket.py"
        assert websocket_path.exists(), f"websocket.py not found: {websocket_path}"

    def test_www_directory_exists(self):
        """Verify www directory exists for frontend panel."""
        www_dir = INTEGRATION_DIR / "www"
        assert www_dir.exists(), f"www directory not found: {www_dir}"
        assert www_dir.is_dir(), f"Expected directory: {www_dir}"

    def test_frontend_panel_exists(self):
        """Verify frontend panel JavaScript file exists."""
        panel_path = INTEGRATION_DIR / "www" / "panel-heimdall.js"
        assert panel_path.exists(), f"Frontend panel not found: {panel_path}"


class TestManifestValidation:
    """Validate manifest.json content."""

    def test_manifest_has_required_fields(self):
        """Verify all required manifest fields."""
        manifest_path = INTEGRATION_DIR / "manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        required = ["domain", "name", "version", "documentation", "issue", "codeowners"]
        for field in required:
            assert field in manifest, f"manifest.json missing required field: {field}"

    def test_manifest_loads_without_errors(self):
        """Verify manifest.json is valid JSON."""
        manifest_path = INTEGRATION_DIR / "manifest.json"
        with open(manifest_path) as f:
            manifest = json.load(f)
        assert isinstance(manifest, dict), "manifest.json must be a JSON object"


class TestConstPyContent:
    """Validate const.py content."""

    def test_const_has_domain(self):
        """Verify const.py defines DOMAIN."""
        const_path = INTEGRATION_DIR / "const.py"
        with open(const_path) as f:
            content = f.read()
        
        assert "DOMAIN" in content, "const.py must define DOMAIN"
        assert "heimdall_battery_sentinel" in content, "const.py must contain domain string"


class TestInitPyContent:
    """Validate __init__.py content."""

    def test_init_has_setup_function(self):
        """Verify __init__.py has async_setup_entry."""
        init_path = INTEGRATION_DIR / "__init__.py"
        with open(init_path) as f:
            content = f.read()
        
        assert "async_setup_entry" in content, "__init__.py must have async_setup_entry"
        assert "_LOGGER" in content, "__init__.py must set up logging"
