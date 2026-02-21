"""Config flow for heimdall_battery_sentinel."""
from __future__ import annotations

import logging
from typing import Any, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_BATTERY_THRESHOLD,
    DEFAULT_NAME,
    DEFAULT_THRESHOLD,
    DOMAIN,
    MAX_THRESHOLD,
    MIN_THRESHOLD,
    STEP_THRESHOLD,
)

_LOGGER = logging.getLogger(__name__)

# Valid threshold values: 5, 10, 15, ..., 100
VALID_THRESHOLDS = list(range(MIN_THRESHOLD, MAX_THRESHOLD + 1, STEP_THRESHOLD))


def _validate_threshold(value: Any) -> int:
    """Validate that a threshold value is an int within allowed range (5–100, step 5).

    Args:
        value: Raw user input.

    Returns:
        Validated integer threshold.

    Raises:
        vol.Invalid: If the value is not a valid threshold.
    """
    try:
        int_value = int(value)
    except (TypeError, ValueError):
        raise vol.Invalid("Threshold must be an integer.")

    if int_value not in VALID_THRESHOLDS:
        raise vol.Invalid(
            f"Threshold must be between {MIN_THRESHOLD} and {MAX_THRESHOLD} "
            f"in steps of {STEP_THRESHOLD}. Valid values: {VALID_THRESHOLDS}"
        )
    return int_value


CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BATTERY_THRESHOLD, default=DEFAULT_THRESHOLD): _validate_threshold,
    }
)


class HeimdallBatterySentinelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for heimdall_battery_sentinel.

    Implements:
    - async_step_user: initial setup with threshold input and validation.
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> dict:
        """Handle the initial setup step.

        Shows a form to collect the battery threshold, validates input, and
        creates the config entry. Prevents duplicate entries.

        Args:
            user_input: Dict with user-provided values, or None on first render.

        Returns:
            FlowResult (form to show user, or entry creation result).
        """
        errors: dict[str, str] = {}

        # Prevent duplicate entries
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            try:
                validated = CONFIG_SCHEMA(user_input)
            except vol.Invalid as exc:
                _LOGGER.debug("Config flow validation error: %s", exc)
                errors["battery_threshold"] = str(exc.msg)
                validated = None

            if not errors and validated is not None:
                _LOGGER.info(
                    "heimdall_battery_sentinel config flow: creating entry with threshold=%d",
                    validated[CONF_BATTERY_THRESHOLD],
                )
                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data={CONF_BATTERY_THRESHOLD: validated[CONF_BATTERY_THRESHOLD]},
                )

        # Render the form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BATTERY_THRESHOLD, default=DEFAULT_THRESHOLD
                    ): vol.In(VALID_THRESHOLDS),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow handler.

        Args:
            config_entry: The current config entry.

        Returns:
            HeimdallOptionsFlow instance.
        """
        return HeimdallOptionsFlow(config_entry)


class HeimdallOptionsFlow(config_entries.OptionsFlow):
    """Handle options updates (e.g., threshold change post-setup).

    Per ADR-007: allows editing threshold via HA options UI after initial setup.
    """

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow.

        Args:
            config_entry: The current config entry.
        """
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[dict[str, Any]] = None
    ) -> dict:
        """Handle the options form.

        Args:
            user_input: Dict with user-provided values, or None on first render.

        Returns:
            FlowResult (form or entry creation result).
        """
        errors: dict[str, str] = {}

        current_threshold = self.config_entry.options.get(
            CONF_BATTERY_THRESHOLD,
            self.config_entry.data.get(CONF_BATTERY_THRESHOLD, DEFAULT_THRESHOLD),
        )

        if user_input is not None:
            try:
                validated = CONFIG_SCHEMA(user_input)
            except vol.Invalid as exc:
                errors["battery_threshold"] = str(exc.msg)
                validated = None

            if not errors and validated is not None:
                _LOGGER.info(
                    "heimdall_battery_sentinel options flow: updating threshold to %d",
                    validated[CONF_BATTERY_THRESHOLD],
                )
                return self.async_create_entry(
                    title="",
                    data={CONF_BATTERY_THRESHOLD: validated[CONF_BATTERY_THRESHOLD]},
                )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BATTERY_THRESHOLD, default=current_threshold
                    ): vol.In(VALID_THRESHOLDS),
                }
            ),
            errors=errors,
        )
