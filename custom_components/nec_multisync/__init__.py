"""The NEC MultiSync integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .api import NecApiError, NecMultisyncApi
from .const import (
    CONF_MONITOR_ID,
    DEFAULT_MONITOR_ID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import NecMultisyncCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.MEDIA_PLAYER,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

type NecConfigEntry = ConfigEntry[NecMultisyncCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: NecConfigEntry) -> bool:
    """Set up NEC MultiSync from a config entry."""
    api = NecMultisyncApi(
        host=entry.data[CONF_HOST],
        monitor_id=entry.data.get(CONF_MONITOR_ID, DEFAULT_MONITOR_ID),
        port=entry.data.get(CONF_PORT, DEFAULT_PORT),
    )

    try:
        await hass.async_add_executor_job(api.connect)
        await hass.async_add_executor_job(api.read_device_info)
        await hass.async_add_executor_job(api.probe)
    except NecApiError as err:
        await hass.async_add_executor_job(api.disconnect)
        raise ConfigEntryNotReady(str(err)) from err

    scan_interval = entry.options.get("scan_interval", DEFAULT_SCAN_INTERVAL)
    coordinator = NecMultisyncCoordinator(hass, entry, api, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: NecConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        await entry.runtime_data.async_shutdown()
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: NecConfigEntry) -> None:
    """Reload the entry when options change (e.g. scan interval)."""
    await hass.config_entries.async_reload(entry.entry_id)
