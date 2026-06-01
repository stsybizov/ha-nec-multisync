"""DataUpdateCoordinator for the NEC MultiSync integration."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NecApiError, NecMultisyncApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class NecMultisyncCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Owns the single blocking connection and serializes all access to it."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: NecMultisyncApi,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api
        # The SDK socket is reused and is not thread-safe, so every access
        # (poll + setters) must go through this lock.
        self._lock = asyncio.Lock()

    async def _async_update_data(self) -> dict[str, Any]:
        async with self._lock:
            try:
                return await self.hass.async_add_executor_job(self.api.poll)
            except NecApiError as err:
                raise UpdateFailed(str(err)) from err

    async def async_execute(self, func: Callable[..., Any], *args: Any) -> None:
        """Run a blocking setter under the lock, then refresh state."""
        async with self._lock:
            try:
                await self.hass.async_add_executor_job(func, *args)
            except NecApiError as err:
                raise UpdateFailed(str(err)) from err
        await self.async_request_refresh()

    async def async_shutdown(self) -> None:
        await super().async_shutdown()
        await self.hass.async_add_executor_job(self.api.disconnect)
