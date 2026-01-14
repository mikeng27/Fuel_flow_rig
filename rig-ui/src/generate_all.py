import os
import yaml
from generate import python_header, markdown, c_header

BASE_DIR = os.path.dirname(__file__)
BUILD_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "build"))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "io_config.yaml")

os.makedirs(BUILD_DIR, exist_ok=True)

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    io_config = yaml.safe_load(f)

# --- Convert YAML into enums/messages ---
enums = {
    "priority": {"values": {"CRITICAL": "0x0", "REALTIME": "0x1"}},
    "destination": {"values": {name.upper(): hex(idx) for idx, name in enumerate(io_config.get("actuators", {}))}},
    "source": {"values": {"SYSTEM_MANAGER": "0x0", "FUEL_DISPENSE": "0x1"}},
}

messages = []
for idx, (sensor_name, sensor_cfg) in enumerate(io_config.get("sensors", {}).items(), start=1):
    messages.append({
        "message_id": idx,
        "name": sensor_name.upper(),
        "type_prefix": sensor_name.title().replace("_", ""),
        "description": sensor_cfg.get("description", sensor_name),
        "dlc": 4,
        "payload": {
            "fields": [
                {"name": "value", "type": "float", "description": "Sensor reading"}
            ]
        }
    })

python_type_mapping = {
    "uint8_t": "int",
    "uint16_t": "int",
    "uint32_t": "int",
    "float": "float",
}

# --- Run generators ---
python_header.generate(enums, messages, BUILD_DIR, python_type_mapping)
markdown.generate(messages, BUILD_DIR)
c_header.generate(messages, BUILD_DIR)

print(f"All files generated in {BUILD_DIR}")
