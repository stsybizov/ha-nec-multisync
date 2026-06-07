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
from .const import OPCODE_HUMAN_SENSING_READING
from .coordinator import NecMultisyncCoordinator
from .entity import NecBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NecConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    entities: list[BinarySensorEntity] = []
    if coordinator.data and coordinator.data.get("fans"):
        entities.append(NecFanProblem(coordinator))
    if OPCODE_HUMAN_SENSING_READING in coordinator.api.supported:
        entities.append(NecHumanPresence(coordinator))
    async_add_entities(entities)


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


class NecHumanPresence(NecBaseEntity, BinarySensorEntity):
    """Occupancy from the panel's built-in human sensor (if fitted)."""

    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_translation_key = "human_presence"

    def __init__(self, coordinator: NecMultisyncCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._identifier}_human_presence"

    @property
    def is_on(self) -> bool | None:
        params = (self.coordinator.data or {}).get("params", {})
        param = params.get(OPCODE_HUMAN_SENSING_READING)
        if param is None:
            return None
        # Non-zero reading means a person was detected.
        return param.current > 0
