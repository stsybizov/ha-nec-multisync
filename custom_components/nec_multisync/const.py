"""Constants and opcode definitions for the NEC MultiSync integration.

Opcode values and value maps are taken from the official NEC "External Control"
command set (mirrored in nec-pd-sdk's ``controls.txt``). Only the subset needed
by this integration is reproduced here, keyed by raw hex opcode so we never
depend on the SDK's constant names.
"""

from __future__ import annotations

from dataclasses import dataclass

DOMAIN = "nec_multisync"

DEFAULT_NAME = "NEC MultiSync"
DEFAULT_PORT = 7142  # fixed on the panel, not configurable
DEFAULT_MONITOR_ID = 1
DEFAULT_SCAN_INTERVAL = 30  # seconds; keeps the <15 min idle session alive

CONF_MONITOR_ID = "monitor_id"
CONF_SOURCES = "sources"

# --- Power states (NEC PD_POWER_STATES) -----------------------------------
POWER_ERROR = 0
POWER_ON = 1
POWER_STANDBY = 2
POWER_SUSPEND = 3
POWER_OFF = 4

POWER_STATE_NAMES: dict[int, str] = {
    POWER_ERROR: "Error",
    POWER_ON: "On",
    POWER_STANDBY: "Standby",
    POWER_SUSPEND: "Suspend",
    POWER_OFF: "Off",
}

# --- Opcodes --------------------------------------------------------------
OPCODE_BACKLIGHT = 0x0010
OPCODE_CONTRAST = 0x0012
OPCODE_COLOR_TEMP = 0x0054
OPCODE_INPUT = 0x0060
OPCODE_VOLUME = 0x0062
OPCODE_SHARPNESS = 0x008C
OPCODE_MUTE = 0x008D
OPCODE_POWER_MODE = 0x00D6  # read only
OPCODE_POWER_SAVE = 0x00E1
OPCODE_KEY_LOCK = 0x00FB
OPCODE_PICTURE_MODE = 0x021A
OPCODE_AUTO_BRIGHTNESS = 0x022D
OPCODE_AUDIO_INPUT = 0x022E
OPCODE_GAMMA = 0x0268
OPCODE_ASPECT = 0x0270
OPCODE_OPTION_SLOT_POWER = 0x1041
OPCODE_AMBIENT_LIGHT = 0x02B5  # "Bright Sensor Read", read only (raw level)
OPCODE_CARBON_FOOTPRINT_KG = 0x1011  # read only
OPCODE_CARBON_SAVINGS_KG = 0x1029  # "no reset" read only

# Audio fine-tuning (panel-side; independent of an external AVR/ARC path)
OPCODE_AUDIO_TREBLE = 0x008F
OPCODE_AUDIO_BASS = 0x0091
OPCODE_AUDIO_BALANCE = 0x0093  # Left .. Right
OPCODE_AUDIO_SURROUND = 0x0234
OPCODE_AUDIO_LINE_OUT = 0x1081  # Fixed / Variable

# Human / occupancy sensing
OPCODE_HUMAN_SENSING_MODE = 0x1075
OPCODE_HUMAN_SENSING_READING = 0x1076  # read only (presence reading)

# --- Input source map (opcode 0x0060), V-series (V754Q/V864Q/V984Q) -------
# Friendly label -> raw value.
INPUT_SOURCES: dict[str, int] = {
    "DisplayPort": 15,
    "DisplayPort2": 16,
    "HDMI1": 17,
    "HDMI2": 18,
    "HDMI3": 130,
    "OPS / Option": 13,
    "Media Player": 135,
    "Compute Module": 136,
}
INPUT_VALUE_TO_NAME: dict[int, str] = {v: k for k, v in INPUT_SOURCES.items()}

# Mute: 1 = Mute, 2 = Unmute (0 = "Unmute (set only)")
MUTE_ON = 1
MUTE_OFF = 2


@dataclass(frozen=True)
class NecSelectDescription:
    """Describes a select entity backed by an enum opcode."""

    key: str
    opcode: int
    options: dict[int, str]  # raw value -> label


@dataclass(frozen=True)
class NecNumberDescription:
    """Describes a number entity backed by a ranged opcode (min 0..max)."""

    key: str
    opcode: int
    unit: str | None = None


@dataclass(frozen=True)
class NecSwitchDescription:
    """Describes a switch entity backed by a two-state opcode."""

    key: str
    opcode: int
    on_value: int = 1
    off_value: int = 0


SELECTS: tuple[NecSelectDescription, ...] = (
    NecSelectDescription(
        key="picture_mode",
        opcode=OPCODE_PICTURE_MODE,
        options={
            1: "sRGB",
            3: "Hi-Bright",
            4: "Standard",
            5: "Cinema",
            6: "ISF-Day",
            7: "ISF-Night",
            8: "Custom 1",
            9: "Custom 2",
        },
    ),
    NecSelectDescription(
        key="aspect",
        opcode=OPCODE_ASPECT,
        options={
            1: "Normal",
            2: "Full",
            3: "Wide",
            4: "Zoom",
            5: "Trim",
            6: "Dynamic",
            7: "1:1",
        },
    ),
    NecSelectDescription(
        key="gamma",
        opcode=OPCODE_GAMMA,
        options={
            1: "Native",
            4: "2.2",
            8: "2.4",
            7: "S Curve",
            5: "DICOM Sim",
            11: "sRGB",
            12: "LStar",
        },
    ),
    NecSelectDescription(
        key="audio_input",
        opcode=OPCODE_AUDIO_INPUT,
        options={
            1: "Audio 1",
            2: "Audio 2",
            3: "Audio 3",
            4: "HDMI",
            6: "TV/Option",
            7: "DisplayPort",
            8: "DisplayPort 2",
            10: "HDMI 2",
            11: "HDMI 3",
            13: "Media Player",
            14: "Compute Module",
        },
    ),
    NecSelectDescription(
        key="option_slot_power",
        opcode=OPCODE_OPTION_SLOT_POWER,
        options={1: "Off (linked)", 2: "On", 3: "Auto"},
    ),
    NecSelectDescription(
        key="audio_surround",
        opcode=OPCODE_AUDIO_SURROUND,
        options={1: "Off", 2: "Low", 3: "High"},
    ),
    NecSelectDescription(
        key="audio_line_out",
        opcode=OPCODE_AUDIO_LINE_OUT,
        options={1: "Fixed", 2: "Variable"},
    ),
)

NUMBERS: tuple[NecNumberDescription, ...] = (
    NecNumberDescription(key="backlight", opcode=OPCODE_BACKLIGHT),
    NecNumberDescription(key="contrast", opcode=OPCODE_CONTRAST),
    NecNumberDescription(key="sharpness", opcode=OPCODE_SHARPNESS),
    NecNumberDescription(key="color_temp", opcode=OPCODE_COLOR_TEMP),
    NecNumberDescription(key="audio_treble", opcode=OPCODE_AUDIO_TREBLE),
    NecNumberDescription(key="audio_bass", opcode=OPCODE_AUDIO_BASS),
    NecNumberDescription(key="audio_balance", opcode=OPCODE_AUDIO_BALANCE),
)

SWITCHES: tuple[NecSwitchDescription, ...] = (
    NecSwitchDescription(key="key_lock", opcode=OPCODE_KEY_LOCK),
    NecSwitchDescription(key="auto_brightness", opcode=OPCODE_AUTO_BRIGHTNESS),
    NecSwitchDescription(key="power_save", opcode=OPCODE_POWER_SAVE),
)

# Diagnostic enum opcodes surfaced as (read-only) sensors with decoded text.
SENSOR_ENUMS: dict[str, NecSelectDescription] = {
    "power_mode": NecSelectDescription(
        key="power_mode",
        opcode=OPCODE_POWER_MODE,
        options={1: "On", 2: "Standby", 3: "Suspend", 4: "Off"},
    ),
}

# Carbon read-only opcodes -> sensor key. Values are reported x10 by the panel.
CARBON_SENSORS: dict[str, int] = {
    "carbon_footprint": OPCODE_CARBON_FOOTPRINT_KG,
    "carbon_savings": OPCODE_CARBON_SAVINGS_KG,
}

# Generic numeric read-only opcodes surfaced as measurement sensors.
# The ambient light reading is a raw level (not calibrated lux), so it is
# exposed without a device class.
NUMERIC_SENSORS: dict[str, int] = {
    "ambient_light": OPCODE_AMBIENT_LIGHT,
}

# All opcodes the api should probe for support during setup.
PROBE_OPCODES: tuple[int, ...] = tuple(
    {
        OPCODE_INPUT,
        OPCODE_VOLUME,
        OPCODE_MUTE,
        *(d.opcode for d in SELECTS),
        *(d.opcode for d in NUMBERS),
        *(d.opcode for d in SWITCHES),
        *(d.opcode for d in SENSOR_ENUMS.values()),
        *CARBON_SENSORS.values(),
        *NUMERIC_SENSORS.values(),
        OPCODE_HUMAN_SENSING_READING,
    }
)
