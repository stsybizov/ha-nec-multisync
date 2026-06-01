<p align="center">
  <img src="custom_components/nec_multisync/brand/logo@2x.png" alt="NEC MultiSync for Home Assistant" width="480">
</p>

# NEC MultiSync — Home Assistant integration

[![Validate](https://github.com/stsybizov/ha-nec-multisync/actions/workflows/validate.yaml/badge.svg)](https://github.com/stsybizov/ha-nec-multisync/actions/workflows/validate.yaml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Custom integration to control **NEC / Sharp NEC large-format displays** over the
network using the official *External Control* protocol (`nec-pd-sdk`).

Developed and tested against the **MultiSync V-series UHD** panels
(**V754Q / V864Q / V984Q**). It should also work with other P/V/X/M-series
displays that speak the same protocol — unsupported features are detected at
setup and simply not exposed.

## Features

A single device is created with these entities (only those the panel supports
are added):

- **Media player** — power on/off, input source (HDMI1/2/3, DisplayPort, OPS,
  Media Player, Compute Module), volume and mute.
- **Select** — picture mode, aspect ratio, gamma, audio input, OPS slot power.
- **Number** — backlight, contrast, sharpness, color temperature.
- **Switch** — key lock, auto brightness, power save.
- **Sensors** (diagnostics) — temperature sensors, fan status, total operating
  time, power-on time, self-diagnosis, carbon footprint / savings, power mode.
- **Binary sensor** — fan problem.

## Requirements on the display

- The display must be reachable on the LAN. Control uses **TCP port 7142**
  (fixed, not configurable on the panel).
- Set **External Control** to *LAN* in the panel's menu.
- For network wake from "off", set **Standby Mode** to the normal (non-ECO)
  setting, otherwise the LAN turns off when the panel is powered off.

## Installation (HACS)

1. HACS → Integrations → ⋮ → *Custom repositories* → add this repository as an
   *Integration*.
2. Install **NEC MultiSync** and restart Home Assistant.
3. *Settings → Devices & Services → Add Integration → NEC MultiSync* and enter
   the display's IP address (and Monitor ID if daisy-chained; default 1).

Manual install: copy `custom_components/nec_multisync` into your HA
`config/custom_components/` folder and restart.

## Options

After adding, open the integration's *Configure* dialog to set:

- **Polling interval** (default 30 s — keeps the panel's 15-minute idle session
  alive).
- **Inputs to expose** as media-player sources.

## Verifying connectivity first

Before installing, you can confirm the panel responds:

```bash
pip install nec-pd-sdk pyserial
python tools/smoke_test.py <display-ip>
```

## Debug logging

Add to `configuration.yaml` and restart:

```yaml
logger:
  default: info
  logs:
    custom_components.nec_multisync: debug
```

## Notes

- The underlying `nec-pd-sdk` is synchronous; the integration keeps one socket
  connection and runs all calls in an executor, serialized by a lock.
- Not all opcodes exist on every model; the integration probes support at setup
  and only creates entities that work.
- `DeviceInfo` is imported from `homeassistant.helpers.entity` (not
  `helpers.device_info`).

## Icon / logo in Home Assistant

Home Assistant loads integration icons from the central
[`home-assistant/brands`](https://github.com/home-assistant/brands) repository,
not from `custom_components`. Until this integration is added there, HA shows a
generic icon (functionality is unaffected).

This repo ships the brand assets ready to go:

- `custom_components/nec_multisync/brand/` — local fallback that silences the
  HACS brand warning.
- `homeassistant_brands/custom_integrations/nec_multisync/` — the exact tree to
  submit to `home-assistant/brands`. Copy its `nec_multisync` folder into that
  repo's `custom_integrations/` and open a PR; once merged, the icon and logo
  appear automatically in HA.

To regenerate the PNGs from source: `python tools/make_brand_assets.py`.

## Credits

Built on the MIT-licensed
[`nec-pd-sdk`](https://github.com/SharpNECDisplaySolutions/necpdsdk) from
Sharp NEC Display Solutions.

## License

Released under the [MIT License](LICENSE).
