"""Standalone connectivity smoke test for a NEC MultiSync display.

Run this BEFORE installing in Home Assistant to confirm the panel answers on
TCP port 7142 and that the protocol works.

    pip install nec-pd-sdk pyserial
    python tools/smoke_test.py 192.168.1.50

It reads identity, power, input, volume and the temperature sensors.
"""

from __future__ import annotations

import sys

from nec_pd_sdk.nec_pd_sdk import NECPD
from nec_pd_sdk.protocol import PDError

OPCODE_INPUT = 0x0060
OPCODE_VOLUME = 0x0062


def main(host: str, monitor_id: int = 1) -> int:
    print(f"Connecting to {host}:7142 (monitor id {monitor_id}) ...")
    pd = NECPD.from_ip_address(host, 7142)
    try:
        pd.helper_set_destination_monitor_id(monitor_id)
        print("Model        :", pd.command_model_name_read())
        print("Serial       :", pd.command_serial_number_read())
        print("Power state  :", pd.command_power_status_read(), "(1=On 2=Standby 3=Suspend 4=Off)")

        inp = pd.command_get_parameter(OPCODE_INPUT)
        print("Input        : value", inp.current_value, "supported" if inp.result == 0 else "UNSUPPORTED")

        vol = pd.command_get_parameter(OPCODE_VOLUME)
        print("Volume       :", vol.current_value, "/", vol.max_value)

        print("Temperatures :", pd.helper_get_temperature_sensor_values())
        print("Fans         :", pd.helper_get_fan_statuses())
        print("Total hours  :", pd.helper_get_total_operating_hours())
        print("Diagnosis    :", pd.helper_self_diagnosis_status_text())
    except PDError as err:
        print("ERROR:", err)
        return 1
    finally:
        pd.close()
    print("OK")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python tools/smoke_test.py <ip> [monitor_id]")
        raise SystemExit(2)
    mid = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    raise SystemExit(main(sys.argv[1], mid))
