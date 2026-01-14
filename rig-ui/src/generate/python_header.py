import os
from typing import Dict, List, Any

# -------------------------------
# Dummy CANMessage classes
# -------------------------------
class CANMessageError(Exception):
    pass

class CANId:
    pass

class CANMessagePayload:
    pass

class CANMessage:
    pass

# -------------------------------
# Writing functions
# -------------------------------
def write_header(f):
    f.write("# Auto-generated Python CAN ID definitions\n")
    f.write("# DO NOT EDIT - generated from io_config.yaml\n\n")

def write_priorities(f, priorities):
    if not priorities:
        return
    f.write("from enum import IntEnum\n\n")
    f.write("class Priority(IntEnum):\n")
    for name, val in priorities.get("values", {}).items():
        f.write(f"    {name} = {int(val, 0):#04b}\n")
    f.write("\n")

def write_destinations(f, destinations):
    if not destinations:
        return
    f.write("class Destination(IntEnum):\n")
    for name, val in destinations.get("values", {}).items():
        f.write(f"    {name} = {int(val, 0):#04b}\n")
    f.write("\n")

def write_sources(f, sources):
    if not sources:
        return
    f.write("class Source(IntEnum):\n")
    for name, val in sources.get("values", {}).items():
        f.write(f"    {name} = {int(val, 0):#04b}\n")
    f.write("\n")

def write_message_ids(f, messages):
    f.write("class MessageID(IntEnum):\n")
    for msg in messages:
        f.write(f"    {msg['name']} = {msg['message_id']:#023b}\n")
    f.write("\n")

def write_dataclasses(f, messages, python_type_mapping):
    for msg in messages:
        if "payload" not in msg:
            continue
        type_prefix = msg.get("type_prefix", msg["name"])
        f.write(f"class {type_prefix}(CANMessagePayload):\n")
        for field in msg["payload"].get("fields", []):
            py_type = python_type_mapping.get(field["type"], "int")
            f.write(f"    {field['name']}: {py_type}\n")
        # Add default struct format (adjust if needed)
        f.write("    _struct_format: str = '<'  # adjust as needed\n\n")

# -------------------------------
# Main generate function
# -------------------------------
def generate(
    enums: Dict[str, Dict[str, Any]],
    messages: List[Dict[str, Any]],
    output_dir: str,
    python_type_mapping: Dict[str, str]
) -> str:
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "can_ids.py")

    with open(path, "w", encoding="utf-8") as f:
        write_header(f)
        write_priorities(f, enums.get("priority"))
        write_destinations(f, enums.get("destination"))
        write_sources(f, enums.get("source"))
        write_message_ids(f, messages)
        write_dataclasses(f, messages, python_type_mapping)

        # Add dummy CANMessage classes
        f.write("""
class CANMessageError(Exception): pass

class CANId: pass

class CANMessagePayload: pass

class CANMessage: pass
""")

    print(f"✅ Python CAN header written to {path}")
    return path

# -------------------------------
# Optional: run directly for testing
# -------------------------------
if __name__ == "__main__":
    # Example usage - generates to build/
    import yaml

    # Assuming your io_config.yaml is at ../../config/io_config.yaml
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config", "io_config.yaml")
    with open(cfg_path, "r") as f:
        io_cfg = yaml.safe_load(f)

    # Minimal enums/messages mapping for example
    enums = {
        "priority": {"values": {"CRITICAL": "0x0", "REALTIME": "0x1"}},
        "destination": {"values": {"SYSTEM_MANAGER": "0x0", "FUEL_DISPENSE": "0x1"}},
        "source": {"values": {"SYSTEM_MANAGER": "0x0", "FUEL_DISPENSE": "0x1"}},
    }

    messages = [
        {"message_id": 0x01, "name": "SET_CONFIG_VERSION", "type_prefix": "ConfigSettings",
         "description": "Set config version", "dlc": 4,
         "payload": {"fields": [{"name": "version", "type": "uint32_t"}]}},
        {"message_id": 0x02, "name": "RESET_MODULE", "type_prefix": "ResetModule",
         "description": "Reset the module", "dlc": 0},
    ]

    python_type_mapping = {"uint32_t": "int", "uint16_t": "int", "uint8_t": "int", "float": "float"}

    build_dir = os.path.join(os.path.dirname(__file__), "..", "..", "build")
    generate(enums, messages, build_dir, python_type_mapping)
