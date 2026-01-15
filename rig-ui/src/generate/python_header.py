# rig-ui/src/generate/python_header.py
import os

def generate(io_config: dict, enums: dict, output_dir: str):
    """
    Generates can_ids.py including base classes, enums, and Event payloads from io_config.yaml
    """
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "can_ids.py")

    with open(path, "w", encoding="utf-8") as f:
        # -------------------------------
        # Base classes
        f.write("# Base CAN classes\n")
        f.write("class CANMessageError(Exception): pass\n")
        f.write("class CANId: pass\n")
        f.write("class CANMessagePayload: pass\n")
        f.write("class CANMessage: pass\n\n")

        # -------------------------------
        # Enums
        f.write("from enum import IntEnum\n\n")

        # Priority
        f.write("class Priority(IntEnum):\n")
        for k, v in enums.get("priority", {}).get("values", {}).items():
            f.write(f"    {k} = {v}\n")
        f.write("\n")

        # Destination — read from io_config + add extra destinations
        f.write("class Destination(IntEnum):\n")
        dests = enums.get("destination", {}).get("values", {}).copy()
        extra_dests = ["SYSTEM_MANAGER", "POWER_MODULE"]
        for extra in extra_dests:
            if extra not in dests:
                dests[extra] = max(dests.values(), default=-1) + 1

        for k, v in dests.items():
            f.write(f"    {k} = {v}\n")
        f.write("\n")

        # Source
        f.write("class Source(IntEnum):\n")
        for k, v in enums.get("source", {}).get("values", {}).items():
            f.write(f"    {k} = {v}\n")
        f.write("\n")

        # MessageID
        f.write("class MessageID(IntEnum):\n")
        for k, v in enums.get("message_id", {}).get("values", {}).items():
            f.write(f"    {k} = {v}\n")
        f.write("\n")

        # -------------------------------
        # Event payload classes
        f.write("# Event payload classes\n")

        # Actuators
        for act_name, act_cfg in io_config.get("actuators", {}).items():
            class_name = "Event" + "".join(word.capitalize() for word in act_name.split("_"))
            f.write(f"class {class_name}(CANMessagePayload):\n")
            typ = act_cfg.get("type", "")
            if typ == "pump":
                f.write("    flow: float\n")
                f.write("    pressure: float\n")
            elif "valve" in typ:
                f.write("    state: bool\n")
            elif typ == "digital_switch":
                f.write("    state: bool\n")
            else:
                f.write("    pass\n")
            f.write("\n")

        # Sensors
        for sens_name, sens_cfg in io_config.get("sensors", {}).items():
            class_name = "Event" + "".join(word.capitalize() for word in sens_name.split("_"))
            f.write(f"class {class_name}(CANMessagePayload):\n")
            typ = sens_cfg.get("type", "")
            if typ in ["flow", "pressure", "temperature", "level", "current", "voltage", "load_cell"]:
                if typ == "pressure_temperature":
                    f.write("    pressure: float\n")
                    f.write("    temperature: float\n")
                else:
                    f.write("    value: float\n")
            else:
                f.write("    value: float\n")  # default
            f.write("\n")

        # Battery / PM
        if "battery_power" in io_config:
            f.write("class EventBatteryPower(CANMessagePayload):\n")
            f.write("    voltage: float\n")
            f.write("    current: float\n")
            f.write("    status: int\n\n")

        if "power_management_module" in io_config:
            f.write("class EventPowerManagementModule(CANMessagePayload):\n")
            f.write("    voltage: float\n")
            f.write("    current: float\n")
            f.write("    status: int\n\n")

        # -------------------------------
        # Generate default Event classes for extra destinations
        for extra in extra_dests:
            class_name = f"Event{extra.capitalize()}"
            f.write(f"class {class_name}(CANMessagePayload):\n")
            f.write("    pass\n\n")

    print(f"✅ Python CAN header written to {path}")
    return path
