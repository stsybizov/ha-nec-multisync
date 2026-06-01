"""Base entity for NEC MultiSync."""

from __future__ import annotations

from homeassistant.const import CONF_HOST
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, format_mac
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import NecMultisyncCoordinator


class NecBaseEntity(CoordinatorEntity[NecMultisyncCoordinator]):
    """Common device info and availability for all NEC entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: NecMultisyncCoordinator) -> None:
        super().__init__(coordinator)
        api = coordinator.api
        entry = coordinator.config_entry
        # Prefer the serial (stable across IP changes); fall back to the
        # configured host, then to the entry_id which is always present.
        identifier = (
            api.serial
            or (entry.data.get(CONF_HOST) if entry else None)
            or (entry.entry_id if entry else "nec_multisync")
        )
        self._identifier = identifier

        connections = set()
        if api.mac:
            connections.add((CONNECTION_NETWORK_MAC, format_mac(api.mac)))

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            connections=connections,
            manufacturer="NEC / Sharp NEC Display Solutions",
            model=api.model or DEFAULT_NAME,
            name=entry.title if entry else DEFAULT_NAME,
            serial_number=api.serial,
            sw_version=api.firmware,
        )
