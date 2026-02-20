"""Config flow for Heimdall Battery Sentinel."""
from homeassistant import config_entries

class HeimdallBatterySentinelConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Heimdall Battery Sentinel."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        # Since we don't have any configuration yet, we just create the entry
        return self.async_create_entry(title="Heimdall Battery Sentinel", data={})