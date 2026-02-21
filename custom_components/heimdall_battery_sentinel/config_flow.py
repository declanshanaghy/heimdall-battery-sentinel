"""Config flow for heimdall_battery_sentinel."""
from homeassistant import config_entries
from .const import DOMAIN

class HeimdallBatterySentinelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for heimdall_battery_sentinel."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        return self.async_create_entry(title="Heimdall Battery Sentinel", data={})