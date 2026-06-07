"""Button platform: sync the display's clock with Home Assistant."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NecConfigEntry
from .coordinator import NecMultisyncCoordinator
from .entity import NecBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NecConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([NecSyncClockButton(entry.runtime_data)])


class NecSyncClockButton(NecBaseEntity, ButtonEntity):
    """Write Home Assistant's current time to the panel's real-time clock."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_translation_key = "sync_clock"
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, coordinator: NecMultisyncCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._identifier}_sync_clock"

    async def async_press(self) -> None:
        await self.coordinator.async_execute(self.coordinator.api.sync_clock)
