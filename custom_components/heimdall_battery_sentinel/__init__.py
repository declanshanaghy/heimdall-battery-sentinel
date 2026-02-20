"""The Heimdall Battery Sentinel integration."""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Heimdall Battery Sentinel component."""
    # Nothing to do in the setup phase yet
    _LOGGER.info("Heimdall Battery Sentinel setup")
    return True