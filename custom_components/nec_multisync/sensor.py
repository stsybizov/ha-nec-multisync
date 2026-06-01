"""Sensor platform: diagnostics (temperature, fans, hours, carbon, status)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NecConfigEntry
from .const import CARBON_SENSORS, NUMERIC_SENSORS, SENSOR_ENUMS
from .coordinator import NecMultisyncCoordinator
from .entity import NecBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NecConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    data = coordinator.data or {}
    entities: list[SensorEntity] = []

    for index in range(len(data.get("temperatures") or [])):
        entities.append(NecTemperatureSensor(coordinator, index))
    for index in range(len(data.get("fans") or [])):
        entities.append(NecFanSensor(coordinator, index))

    if data.get("total_operating_hours") is not None:
        entities.append(
            NecHoursSensor(coordinator, "total_operating_hours")
        )
    if data.get("power_on_hours") is not None:
        entities.append(NecHoursSensor(coordinator, "power_on_hours"))
    if data.get("diagnosis"):
        entities.append(NecDiagnosisSensor(coordinator))

    for key, opcode in CARBON_SENSORS.items():
        if opcode in coordinator.api.supported:
            entities.append(NecCarbonSensor(coordinator, key, opcode))

    for key, opcode in NUMERIC_SENSORS.items():
        if opcode in coordinator.api.supported:
            entities.append(NecNumericSensor(coordinator, key, opcode))

    for key, desc in SENSOR_ENUMS.items():
        if desc.opcode in coordinator.api.supported:
            entities.append(NecEnumSensor(coordinator, key, desc.opcode, desc.options))

    async_add_entities(entities)


class _NecSensorBase(NecBaseEntity, SensorEntity):
    def __init__(self, coordinator: NecMultisyncCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{self._identifier}_{key}"
        self._attr_translation_key = key

    @property
    def _data(self) -> dict[str, Any]:
        return self.coordinator.data or {}


class NecTemperatureSensor(_NecSensorBase):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: NecMultisyncCoordinator, index: int) -> None:
        super().__init__(coordinator, f"temperature_{index + 1}")
        self._index = index
        self._attr_translation_key = "temperature"
        self._attr_translation_placeholders = {"number": str(index + 1)}

    @property
    def native_value(self) -> float | None:
        temps = self._data.get("temperatures") or []
        return temps[self._index] if self._index < len(temps) else None


class NecFanSensor(_NecSensorBase):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: NecMultisyncCoordinator, index: int) -> None:
        super().__init__(coordinator, f"fan_{index + 1}")
        self._index = index
        self._attr_translation_key = "fan"
        self._attr_translation_placeholders = {"number": str(index + 1)}

    @property
    def native_value(self) -> str | None:
        fans = self._data.get("fans") or []
        return fans[self._index] if self._index < len(fans) else None


class NecHoursSensor(_NecSensorBase):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> float | None:
        return self._data.get(self._attr_translation_key)


class NecDiagnosisSensor(_NecSensorBase):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: NecMultisyncCoordinator) -> None:
        super().__init__(coordinator, "diagnosis")

    @property
    def native_value(self) -> str | None:
        text = self._data.get("diagnosis")
        return text.strip("; ").strip() if text else None


class NecCarbonSensor(_NecSensorBase):
    _attr_native_unit_of_measurement = "kg"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: NecMultisyncCoordinator, key: str, opcode: int
    ) -> None:
        super().__init__(coordinator, key)
        self._opcode = opcode

    @property
    def native_value(self) -> float | None:
        param = self._data.get("params", {}).get(self._opcode)
        return param.current if param else None


class NecNumericSensor(_NecSensorBase):
    """A raw numeric read-only opcode (e.g. ambient light level)."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self, coordinator: NecMultisyncCoordinator, key: str, opcode: int
    ) -> None:
        super().__init__(coordinator, key)
        self._opcode = opcode

    @property
    def native_value(self) -> int | None:
        param = self._data.get("params", {}).get(self._opcode)
        return param.current if param else None


class NecEnumSensor(_NecSensorBase):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: NecMultisyncCoordinator,
        key: str,
        opcode: int,
        options: dict[int, str],
    ) -> None:
        super().__init__(coordinator, key)
        self._opcode = opcode
        self._options = options

    @property
    def native_value(self) -> str | None:
        param = self._data.get("params", {}).get(self._opcode)
        if param is None:
            return None
        return self._options.get(param.current, str(param.current))
