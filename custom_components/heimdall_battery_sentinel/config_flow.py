"""Config flow for Heimdall Battery Sentinel."""

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

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional("threshold", default=DEFAULT_THRESHOLD): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_THRESHOLD, max=MAX_THRESHOLD),
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate the user input."""
    # Validate threshold is multiple of THRESHOLD_STEP
    threshold = data.get("threshold", DEFAULT_THRESHOLD)
    if threshold % THRESHOLD_STEP != 0:
        return {"threshold": f"Threshold must be a multiple of {THRESHOLD_STEP}"}
    
    return {}


class HeimdallBatterySentinelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Heimdall Battery Sentinel."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            errors = await validate_input(self.hass, user_input)
            
            if not errors:
                return self.async_create_entry(
                    title="Heimdall Battery Sentinel",
                    data=user_input,
                )
        
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
