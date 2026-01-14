import os
from typing import List, Dict, Any

# -------------------------------
# Main generate function
# -------------------------------
def generate(messages: List[Dict[str, Any]], output_dir: str) -> str:
    """
    Generate a Markdown file listing CAN messages and payloads.
    """
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "can_messages.md")

    with open(path, "w", encoding="utf-8") as f:
        f.write("# Auto-generated CAN Message Definitions\n")
        f.write("**DO NOT EDIT** - generated from io_config.yaml\n\n")

        for msg in messages:
            f.write(f"## {msg['name']}\n")
            f.write(f"- Message ID: `{msg['message_id']}`\n")
            f.write(f"- Description: {msg.get('description', 'N/A')}\n")
            f.write(f"- DLC: {msg.get('dlc', 'N/A')}\n")

            payload = msg.get("payload")
            if payload:
                f.write("- Payload fields:\n")
                for field in payload.get("fields", []):
                    f.write(f"  - {field['name']}: {field['type']}\n")
            f.write("\n")

    print(f"✅ Markdown CAN message documentation written to {path}")
    return path


# -------------------------------
# Optional direct run for testing
# -------------------------------
if __name__ == "__main__":
    import yaml

    # Path to your io_config.yaml
    cfg_path = os.path.join(os.path.dirname(__file__), "..", "config", "io_config.yaml")
    with open(cfg_path, "r") as f:
        io_cfg = yaml.safe_load(f)

    # Example minimal messages for testing
    messages = [
        {"message_id": 0x01, "name": "SET_CONFIG_VERSION", "description": "Set config version", "dlc": 4,
         "payload": {"fields": [{"name": "version", "type": "uint32_t"}]}},
        {"message_id": 0x02, "name": "RESET_MODULE", "description": "Reset the module", "dlc": 0},
    ]

    build_dir = os.path.join(os.path.dirname(__file__), "..", "..", "build")
    generate(messages, build_dir)
