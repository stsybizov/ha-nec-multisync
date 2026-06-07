"""Synchronous client wrapper around nec-pd-sdk for a single NEC display.

All methods here are blocking (socket I/O) and are expected to be called from an
executor by the coordinator. The wrapper owns a single ``NECPD`` connection,
probes which opcodes the connected model supports, and reconnects on failure
(the SDK's own ``reopen`` is unreliable, so we recreate the connection).

The SDK wraps every command in a ``@retry`` decorator that can return ``None``
instead of raising when a command repeatedly fails. Every call site below
therefore treats a ``None`` reply as "no data" rather than assuming a
namedtuple is always returned.
"""

from __future__ import annotations

import logging
from typing import Any

from .const import DEFAULT_PORT, PROBE_OPCODES

_LOGGER = logging.getLogger(__name__)


class NecApiError(Exception):
    """Raised when communication with the display fails."""


class NecParam:
    """A probed opcode parameter: current value and reported maximum."""

    __slots__ = ("current", "maximum")

    def __init__(self, current: int, maximum: int) -> None:
        self.current = current
        self.maximum = maximum


class NecMultisyncApi:
    """Blocking client for one NEC large-format display over LAN."""

    def __init__(self, host: str, monitor_id: int, port: int = DEFAULT_PORT) -> None:
        self._host = host
        self._port = port
        self._monitor_id = monitor_id
        self._pd: Any = None

        # Static device identity, filled in by read_device_info().
        self.model: str | None = None
        self.serial: str | None = None
        self.mac: str | None = None
        self.firmware: str | None = None
        self.ip_address: str | None = None

        # Opcodes the connected model actually supports (populated by probe()).
        self.supported: set[int] = set()

    # -- connection ---------------------------------------------------------
    def connect(self) -> None:
        """Open (or reopen) the connection and set the destination monitor."""
        # Imported lazily so HA only needs the requirement at runtime.
        from nec_pd_sdk.nec_pd_sdk import NECPD  # noqa: PLC0415
        from nec_pd_sdk.protocol import PDError  # noqa: PLC0415

        self.disconnect()
        try:
            pd = NECPD.from_ip_address(self._host, self._port)
            pd.helper_set_destination_monitor_id(self._monitor_id)
        except (PDError, OSError) as err:
            raise NecApiError(f"Cannot connect to {self._host}: {err}") from err
        self._pd = pd

    def disconnect(self) -> None:
        """Close the connection if open."""
        if self._pd is not None:
            try:
                self._pd.close()
            except Exception:  # noqa: BLE001 - best effort on teardown
                pass
            self._pd = None

    def _ensure(self) -> Any:
        if self._pd is None:
            self.connect()
        return self._pd

    def _on_error(self, err: Exception) -> NecApiError:
        """Drop the connection so the next call reconnects."""
        self.disconnect()
        if isinstance(err, NecApiError):
            return err
        return NecApiError(str(err))

    # -- identity & capabilities -------------------------------------------
    def read_device_info(self) -> None:
        """Read model/serial/MAC/firmware once for the device registry."""
        from nec_pd_sdk.protocol import PDError  # noqa: PLC0415

        pd = self._ensure()
        try:
            self.model = _clean(pd.command_model_name_read())
            self.serial = _clean(pd.command_serial_number_read())
        except (PDError, OSError) as err:
            raise self._on_error(err) from err

        # Optional identity fields - never fatal.
        try:
            # Returns a (mac_string, length) tuple, mac already dash-hex.
            self.mac = _format_mac(pd.command_lan_mac_address_read())
        except (PDError, OSError):
            self.mac = None
        try:
            # Returns a list of version strings, e.g. ['R2.401', 'V1.005', ...];
            # element 0 is the main firmware version.
            versions = pd.helper_firmware_versions_list()
            self.firmware = _clean(versions[0]) if versions else None
        except (PDError, OSError, IndexError, TypeError):
            self.firmware = None
        try:
            # command_ip_address_read returns (ip_string, ip_version).
            result = pd.command_ip_address_read()
            self.ip_address = _first(result)
        except (PDError, OSError):
            self.ip_address = None

    def probe(self) -> None:
        """Determine which opcodes the connected display supports."""
        from nec_pd_sdk.protocol import PDError  # noqa: PLC0415

        pd = self._ensure()
        supported: set[int] = set()
        for opcode in PROBE_OPCODES:
            try:
                reply = pd.command_get_parameter(opcode)
            except (PDError, OSError):
                continue
            # reply is None when the SDK gave up after repeated timeouts.
            if reply is not None and reply.result == 0:  # 0x00 == supported
                supported.add(opcode)
        self.supported = supported
        _LOGGER.debug("Probed %d supported opcodes", len(supported))

    # -- generic parameter access ------------------------------------------
    def get_parameter(self, opcode: int) -> NecParam | None:
        """Return current/max for an opcode, or None if unsupported/no reply."""
        from nec_pd_sdk.protocol import PDError  # noqa: PLC0415

        pd = self._ensure()
        try:
            reply = pd.command_get_parameter(opcode)
        except (PDError, OSError) as err:
            raise self._on_error(err) from err
        if reply is None or reply.result != 0:
            return None
        return NecParam(reply.current_value, reply.max_value)

    def set_parameter(self, opcode: int, value: int) -> None:
        from nec_pd_sdk.protocol import PDError  # noqa: PLC0415

        pd = self._ensure()
        try:
            pd.command_set_parameter(opcode, int(value))
        except (PDError, OSError) as err:
            raise self._on_error(err) from err

    # -- power --------------------------------------------------------------
    def get_power(self) -> int | None:
        from nec_pd_sdk.protocol import PDError  # noqa: PLC0415

        pd = self._ensure()
        try:
            return pd.command_power_status_read()
        except (PDError, OSError) as err:
            raise self._on_error(err) from err

    def set_power(self, state: int) -> None:
        from nec_pd_sdk.protocol import PDError  # noqa: PLC0415

        pd = self._ensure()
        try:
            pd.command_power_status_set(int(state))
        except (PDError, OSError) as err:
            raise self._on_error(err) from err

    # -- clock --------------------------------------------------------------
    def sync_clock(self) -> None:
        """Write the local time to the display's real-time clock."""
        from datetime import datetime  # noqa: PLC0415

        from nec_pd_sdk.protocol import PDError  # noqa: PLC0415

        pd = self._ensure()
        try:
            pd.helper_date_and_time_write(datetime.now())
        except (PDError, OSError) as err:
            raise self._on_error(err) from err

    # -- polling ------------------------------------------------------------
    def poll(self) -> dict[str, Any]:
        """Read all supported state in one pass.

        Retries once with a fresh connection if the first attempt fails, so a
        single swallowed timeout (the SDK turns repeated timeouts into ``None``)
        does not wedge setup or mark the device unavailable. Raises
        ``NecApiError`` only if the retry also fails.
        """
        try:
            return self._poll_once()
        except NecApiError as first_err:
            _LOGGER.debug("poll failed (%s); reconnecting and retrying", first_err)
            try:
                self.connect()
                return self._poll_once()
            except NecApiError as second_err:
                raise second_err from first_err

    def _poll_once(self) -> dict[str, Any]:
        from nec_pd_sdk.protocol import PDError  # noqa: PLC0415

        pd = self._ensure()
        data: dict[str, Any] = {"params": {}}
        try:
            power = pd.command_power_status_read()
            if power is None:
                # No reply at all -> drop the connection and fail this cycle.
                raise self._on_error(NecApiError("no reply to power status read"))
            data["power"] = power

            for opcode in self.supported:
                reply = pd.command_get_parameter(opcode)
                if reply is not None and reply.result == 0:
                    data["params"][opcode] = NecParam(
                        reply.current_value, reply.max_value
                    )

            data["temperatures"] = _safe_list(pd.helper_get_temperature_sensor_values)
            data["fans"] = _safe_list(pd.helper_get_fan_statuses)
            data["total_operating_hours"] = _safe(pd.helper_get_total_operating_hours)
            data["power_on_hours"] = _safe(pd.helper_get_power_on_hours)
            data["diagnosis"] = _safe(pd.helper_self_diagnosis_status_text)
            data["display_time"] = _read_display_time(pd)
            data["signal"] = _read_signal(pd)
        except (PDError, OSError) as err:
            raise self._on_error(err) from err
        return data


def _clean(value: Any) -> str | None:
    """Normalize a model/serial/firmware field (SDK may return bytes)."""
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("ascii", errors="replace")
    return str(value).strip().strip("\x00").strip() or None


def _format_mac(value: Any) -> str | None:
    """Normalize the MAC the SDK returns.

    ``command_lan_mac_address_read`` returns a ``(mac_string, length)`` tuple,
    with the MAC already as dash-separated hex, e.g. ``('d4-92-34-82-5f-cd', 4)``.
    Home Assistant's ``format_mac`` later canonicalizes the separator.
    """
    if not value:
        return None
    if isinstance(value, (tuple, list)):
        value = value[0] if value else None
    if isinstance(value, (bytes, bytearray)):
        return ":".join(f"{b:02x}" for b in value)
    return _clean(value)


def _first(value: Any) -> Any:
    """Return element 0 of a tuple/list, else the value itself."""
    if isinstance(value, (tuple, list)):
        return value[0] if value else None
    return value


def _read_display_time(pd: Any) -> str | None:
    """Return the display RTC time as 'HH:MM', or None if unavailable.

    The SDK reports the time-of-day fields; we surface the wall clock so the
    user can confirm the panel's schedule clock is in sync.
    """
    try:
        dt = pd.command_date_and_time_read()
    except Exception:  # noqa: BLE001 - optional diagnostics
        return None
    if dt is None:
        return None
    try:
        return f"{dt.hour:02d}:{dt.minute:02d}"
    except (AttributeError, TypeError, ValueError):
        return None


def _read_signal(pd: Any) -> dict[str, float] | None:
    """Return current input timing as {'h_khz', 'v_hz'}, or None if no signal."""
    try:
        result = pd.command_get_timing_report()
    except Exception:  # noqa: BLE001 - optional diagnostics
        return None
    if not result:
        return None
    try:
        _status, h_freq, v_freq = result
    except (TypeError, ValueError):
        return None
    # SDK reports both frequencies scaled by 100.
    return {"h_khz": h_freq / 100.0, "v_hz": v_freq / 100.0}


def _safe(func: Any) -> Any:
    try:
        return func()
    except Exception:  # noqa: BLE001 - optional diagnostics, never fatal
        return None


def _safe_list(func: Any) -> list:
    result = _safe(func)
    return list(result) if result else []
