"""Switch platform: two-state opcodes (key lock, auto brightness, power save)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NecConfigEntry
from .const import SWITCHES, NecSwitchDescription
from .coordinator import NecMultisyncCoordinator
from .entity import NecBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NecConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        NecSwitch(coordinator, desc)
        for desc in SWITCHES
        if desc.opcode in coordinator.api.supported
    )


class NecSwitch(NecBaseEntity, SwitchEntity):
    """A display setting that is on or off."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self, coordinator: NecMultisyncCoordinator, desc: NecSwitchDescription
    ) -> None:
        super().__init__(coordinator)
        self._desc = desc
        self._attr_unique_id = f"{self._identifier}_{desc.key}"
        self._attr_translation_key = desc.key

    @property
    def is_on(self) -> bool | None:
        params = (self.coordinator.data or {}).get("params", {})
        param = params.get(self._desc.opcode)
        if param is None:
            return None
        return param.current == self._desc.on_value

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_execute(
            self.coordinator.api.set_parameter, self._desc.opcode, self._desc.on_value
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_execute(
            self.coordinator.api.set_parameter, self._desc.opcode, self._desc.off_value
        )
