import os
from typing import List, Dict, Any

# -------------------------------
# Main generate function
# -------------------------------
def generate(messages: List[Dict[str, Any]], output_dir: str) -> str:
    """
    Generate a C header file for CAN messages.
    """
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "can_ids.h")

    with open(path, "w", encoding="utf-8") as f:
        f.write("// Auto-generated CAN ID definitions\n")
        f.write("// Do not edit manually\n\n")
        f.write("#pragma once\n\n")
        f.write("#include <stdint.h>\n\n")

        f.write("typedef enum {\n")
        for msg in messages:
            msg_id = msg['message_id']
            f.write(f"    {msg['name']} = {msg_id},\n")
        f.write("} MessageID;\n\n")

    print(f"✅ C header CAN definitions written to {path}")
    return path


# -------------------------------
# Optional direct run for testing
# -------------------------------
if __name__ == "__main__":
    import yaml
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config", "io_config.yaml")
    with open(cfg_path, "r") as f:
        io_cfg = yaml.safe_load(f)

    messages = [
        {"message_id": 0x01, "name": "SET_CONFIG_VERSION"},
        {"message_id": 0x02, "name": "RESET_MODULE"}
    ]

    build_dir = os.path.join(os.path.dirname(__file__), "..", "..", "build")
    generate(messages, build_dir)
