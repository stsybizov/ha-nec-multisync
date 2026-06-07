# Changelog

## 0.2.0

Added (all probed per model — unsupported ones are skipped):

- **Button** — sync the panel's real-time clock with Home Assistant.
- **Binary sensor** — presence, on panels fitted with a human sensor.
- **Sensors** — IP address, display clock, and current-input H/V signal
  frequency.
- **Numbers** — audio treble, bass, balance.
- **Selects** — surround sound, audio line out.

Verified end-to-end on a real MultiSync V864Q.

## 0.1.0

Initial release. HACS-compatible integration for NEC / Sharp NEC MultiSync
large-format displays (V754Q / V864Q / V984Q) over LAN, built on the official
`nec-pd-sdk` External Control protocol.

- **media_player** — power, input source, volume, mute
- **select** — picture mode, aspect ratio, gamma, audio input, OPS slot power
- **number** — backlight, contrast, sharpness, color temperature
- **switch** — key lock, auto brightness, power save
- **sensor** — temperatures, fans, operating hours, ambient light, carbon
  footprint/savings, self-diagnosis, power mode
- **binary_sensor** — fan problem
