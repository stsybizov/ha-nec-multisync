# NEC MultiSync

Control **NEC / Sharp NEC large-format displays** from Home Assistant over the
network, using the official *External Control* protocol.

Developed and verified on the **MultiSync V-series UHD** panels
(**V754Q / V864Q / V984Q**). Other P/V/X/M-series displays speaking the same
protocol should also work — unsupported features are detected at setup and
simply not shown.

## What you get

A single device with (only the entities your panel supports are created):

- **Media player** — power, input source, volume, mute
- **Select** — picture mode, aspect ratio, gamma, audio input, OPS slot power
- **Number** — backlight, contrast, sharpness, color temperature
- **Switch** — key lock, auto brightness, power save
- **Sensors** — temperatures, fans, operating hours, ambient light, carbon
  footprint/savings, self-diagnosis, power mode
- **Binary sensor** — fan problem

## Setup

1. Make sure the display is on the LAN and **External Control** is set to *LAN*.
2. Add the integration and enter the display's IP address.

Configuration is done entirely through the UI — no YAML.
