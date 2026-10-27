import os
from pathlib import Path

SETTING_NAMES = (
    "SUBTITLE_INTERFACE",
    "SUBTITLE_WHISPER_MODEL",
    "SUBTITLE_WHISPER_DEVICE",
    "SUBTITLE_WHISPER_COMPUTE_TYPE",
    "SUBTITLE_WHISPER_CPU_THREADS",
    "SUBTITLE_OLLAMA_MODEL",
    "SUBTITLE_OLLAMA_URL",
)


def load_settings(config_path=None):
    settings = {}
    config_path = Path(config_path) if config_path else Path(__file__).with_name(".env")
    if config_path.is_file():
        for line in config_path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, value = line.split("=", 1)
            settings[name.strip()] = value.strip().strip("\"'")

    for name in SETTING_NAMES:
        if name in os.environ:
            settings[name] = os.environ[name]
    return settings


def choose_interface(default=None):
    default = default or load_settings().get("SUBTITLE_INTERFACE", "gui")
    default = default.lower()
    if default not in {"gui", "cli"}:
        default = "gui"

    while True:
        print("\nChoose interface:")
        print("1. GUI file dialogs")
        print("2. CLI only")
        choice = input(f"Choice [default: {default}]: ").strip().lower()
        if not choice:
            return default
        if choice in {"1", "gui", "g"}:
            return "gui"
        if choice in {"2", "cli", "c"}:
            return "cli"
        print("Choose 1 for GUI or 2 for CLI.")