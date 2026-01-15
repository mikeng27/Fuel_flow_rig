# rig-ui/src/generate_all.py
import os
import yaml
from generate.python_header import generate

# Paths
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
IO_CONFIG_PATH = os.path.join(SRC_DIR, "config", "io_config.yaml")
OUTPUT_DIR = SRC_DIR  # generate can_ids.py directly in rig-ui/src

# Load io_config.yaml
with open(IO_CONFIG_PATH, "r", encoding="utf-8") as f:
    io_config = yaml.safe_load(f)

# Minimal enums (you can extend later)
enums = {
    "priority": {"values": {"CRITICAL": 0, "REALTIME": 1}},
    "destination": {"values": {act.upper(): idx for idx, act in enumerate(io_config.get("actuators", {}))}},
    "source": {"values": {"SYSTEM_MANAGER": 0, "FUEL_DISPENSE": 1, "POWER_MODULE": 2}},
    "message_id": {"values": {sensor.upper(): idx+1 for idx, sensor in enumerate(io_config.get("sensors", {}))}}
}

# Mapping YAML types to Python types
python_type_mapping = {
    "float": "float",
    "int": "int",
    "bool": "bool",
    "str": "str",
}

# Generate the Python CAN header
generate(io_config, enums, OUTPUT_DIR)

print(f"✅ can_ids.py regenerated in {OUTPUT_DIR}")
