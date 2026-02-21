"""The heimdall_battery_sentinel integration."""
import logging

DOMAIN = "heimdall_battery_sentinel"
LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    """Set up the heimdall_battery_sentinel component."""
    LOGGER.info("Setting up heimdall_battery_sentinel integration")
    return True