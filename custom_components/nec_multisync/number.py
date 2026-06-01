"""Number platform: ranged opcodes (backlight, contrast, sharpness, color temp)."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NecConfigEntry
from .const import NUMBERS, NecNumberDescription
from .coordinator import NecMultisyncCoordinator
from .entity import NecBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NecConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        NecNumber(coordinator, desc)
        for desc in NUMBERS
        if desc.opcode in coordinator.api.supported
    )


class NecNumber(NecBaseEntity, NumberEntity):
    """A 0..max display parameter exposed as a slider."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = 0
    _attr_native_step = 1

    def __init__(
        self, coordinator: NecMultisyncCoordinator, desc: NecNumberDescription
    ) -> None:
        super().__init__(coordinator)
        self._desc = desc
        self._attr_unique_id = f"{self._identifier}_{desc.key}"
        self._attr_translation_key = desc.key
        if desc.unit:
            self._attr_native_unit_of_measurement = desc.unit

    def _param(self):
        params = (self.coordinator.data or {}).get("params", {})
        return params.get(self._desc.opcode)

    @property
    def native_max_value(self) -> float:
        param = self._param()
        return float(param.maximum) if param and param.maximum else 100.0

    @property
    def native_value(self) -> float | None:
        param = self._param()
        return float(param.current) if param else None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_execute(
            self.coordinator.api.set_parameter, self._desc.opcode, int(value)
        )
