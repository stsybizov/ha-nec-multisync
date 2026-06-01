"""Binary sensor platform: fan fault derived from fan status."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    coordinator = entry.runtime_data
    if coordinator.data and coordinator.data.get("fans"):
        async_add_entities([NecFanProblem(coordinator)])


class NecFanProblem(NecBaseEntity, BinarySensorEntity):
    """On when any cooling fan reports an error."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_translation_key = "fan_problem"

    def __init__(self, coordinator: NecMultisyncCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._identifier}_fan_problem"

    @property
    def is_on(self) -> bool | None:
        fans = (self.coordinator.data or {}).get("fans")
        if not fans:
            return None
        return any("error" in str(status).lower() for status in fans)
