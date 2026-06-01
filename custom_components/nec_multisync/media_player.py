"""Media player platform: power, input source, volume and mute."""

from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import NecConfigEntry
from .const import (
    CONF_SOURCES,
    INPUT_SOURCES,
    INPUT_VALUE_TO_NAME,
    MUTE_OFF,
    MUTE_ON,
    OPCODE_INPUT,
    OPCODE_MUTE,
    OPCODE_VOLUME,
    POWER_OFF,
    POWER_ON,
)
from .entity import NecBaseEntity

_POWER_TO_STATE = {
    POWER_ON: MediaPlayerState.ON,
    2: MediaPlayerState.STANDBY,
    3: MediaPlayerState.STANDBY,
    POWER_OFF: MediaPlayerState.OFF,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: NecConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([NecMediaPlayer(entry.runtime_data, entry)])


class NecMediaPlayer(NecBaseEntity, MediaPlayerEntity):
    """The main controllable entity for the display."""

    _attr_name = None  # use the device name
    _attr_supported_features = (
        MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
        | MediaPlayerEntityFeature.SELECT_SOURCE
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.VOLUME_STEP
        | MediaPlayerEntityFeature.VOLUME_MUTE
    )

    def __init__(self, coordinator, entry: NecConfigEntry) -> None:
        super().__init__(coordinator)
        identifier = coordinator.api.serial or entry.data["host"]
        self._attr_unique_id = f"{identifier}_media_player"
        configured = entry.options.get(CONF_SOURCES) or list(INPUT_SOURCES)
        self._attr_source_list = [s for s in INPUT_SOURCES if s in configured]

    @property
    def _params(self) -> dict:
        return (self.coordinator.data or {}).get("params", {})

    @property
    def state(self) -> MediaPlayerState | None:
        power = (self.coordinator.data or {}).get("power")
        return _POWER_TO_STATE.get(power)

    @property
    def source(self) -> str | None:
        param = self._params.get(OPCODE_INPUT)
        if param is None:
            return None
        return INPUT_VALUE_TO_NAME.get(param.current, f"Input {param.current}")

    @property
    def volume_level(self) -> float | None:
        param = self._params.get(OPCODE_VOLUME)
        if param is None or not param.maximum:
            return None
        return param.current / param.maximum

    @property
    def is_volume_muted(self) -> bool | None:
        param = self._params.get(OPCODE_MUTE)
        if param is None:
            return None
        return param.current == MUTE_ON

    async def async_turn_on(self) -> None:
        await self.coordinator.async_execute(self.coordinator.api.set_power, POWER_ON)

    async def async_turn_off(self) -> None:
        await self.coordinator.async_execute(self.coordinator.api.set_power, POWER_OFF)

    async def async_select_source(self, source: str) -> None:
        value = INPUT_SOURCES.get(source)
        if value is None:
            return
        await self.coordinator.async_execute(
            self.coordinator.api.set_parameter, OPCODE_INPUT, value
        )

    async def async_set_volume_level(self, volume: float) -> None:
        param = self._params.get(OPCODE_VOLUME)
        maximum = param.maximum if param and param.maximum else 100
        await self.coordinator.async_execute(
            self.coordinator.api.set_parameter, OPCODE_VOLUME, round(volume * maximum)
        )

    async def async_volume_up(self) -> None:
        await self._step_volume(+1)

    async def async_volume_down(self) -> None:
        await self._step_volume(-1)

    async def _step_volume(self, direction: int) -> None:
        param = self._params.get(OPCODE_VOLUME)
        if param is None:
            return
        maximum = param.maximum or 100
        new_value = max(0, min(maximum, param.current + direction))
        await self.coordinator.async_execute(
            self.coordinator.api.set_parameter, OPCODE_VOLUME, new_value
        )

    async def async_mute_volume(self, mute: bool) -> None:
        await self.coordinator.async_execute(
            self.coordinator.api.set_parameter,
            OPCODE_MUTE,
            MUTE_ON if mute else MUTE_OFF,
        )
