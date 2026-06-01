"""Select platform: enum opcodes (picture mode, aspect, gamma, etc.)."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NecConfigEntry
from .const import SELECTS, NecSelectDescription
from .coordinator import NecMultisyncCoordinator
from .entity import NecBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NecConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        NecSelect(coordinator, desc)
        for desc in SELECTS
        if desc.opcode in coordinator.api.supported
    )


class NecSelect(NecBaseEntity, SelectEntity):
    """A display setting with a fixed set of values."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self, coordinator: NecMultisyncCoordinator, desc: NecSelectDescription
    ) -> None:
        super().__init__(coordinator)
        self._desc = desc
        self._attr_unique_id = f"{self._identifier}_{desc.key}"
        self._attr_translation_key = desc.key
        self._attr_options = list(desc.options.values())

    @property
    def current_option(self) -> str | None:
        params = (self.coordinator.data or {}).get("params", {})
        param = params.get(self._desc.opcode)
        if param is None:
            return None
        return self._desc.options.get(param.current)

    async def async_select_option(self, option: str) -> None:
        for value, label in self._desc.options.items():
            if label == option:
                await self.coordinator.async_execute(
                    self.coordinator.api.set_parameter, self._desc.opcode, value
                )
                return
