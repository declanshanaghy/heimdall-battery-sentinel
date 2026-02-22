"""Options flow for Heimdall Battery Sentinel."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DEFAULT_THRESHOLD,
    DOMAIN,
    MAX_THRESHOLD,
    MIN_THRESHOLD,
    THRESHOLD_STEP,
)
from .helpers import get_clusters

_LOGGER = logging.getLogger(__name__)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional("threshold", default=DEFAULT_THRESHOLD): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_THRESHOLD, max=MAX_THRESHOLD),
        ),
    }
)


async def validate_options(hass: HomeAssistant, options: dict[str, Any]) -> dict[str, str]:
    """Validate options."""
    threshold = options.get("threshold", DEFAULT_THRESHOLD)
    if threshold % THRESHOLD_STEP != 0:
        return {"threshold": f"Threshold must be a multiple of {THRESHOLD_STEP}"}
    return {}


class HeimdallBatterySentinelOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Heimdall Battery Sentinel."""

    VERSION = 1

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage options."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            errors = await validate_options(self.hass, user_input)
            
            if not errors:
                return self.async_create_entry(title="", data=user_input)
        
        # Get current options
        entry = self.hass.config_entries.async_get_entry(self.handler)
        current_threshold = DEFAULT_THRESHOLD
        
        if entry and entry.options:
            current_threshold = entry.options.get("threshold", DEFAULT_THRESHOLD)
        
        options_schema = vol.Schema(
            {
                vol.Optional("threshold", default=current_threshold): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_THRESHOLD, max=MAX_THRESHOLD),
                ),
            }
        )
        
        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
        )
