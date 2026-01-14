import os
import yaml

def load_config(filename="io_config.yaml"):
    """
    Load a YAML config file from 'src/config/' folder regardless of working directory.
    """
    # Get the folder of the 'src' directory
    src_dir = os.path.dirname(os.path.abspath(__file__))  # config_loader.py is in src/
    config_dir = os.path.join(src_dir, "config")
    yaml_path = os.path.join(config_dir, filename)

    if not os.path.isfile(yaml_path):
        raise FileNotFoundError(
            f"YAML config file not found: {yaml_path}\n"
            "Make sure 'io_config.yaml' exists in 'src/config/'"
        )

    with open(yaml_path, "r") as f:
        return yaml.safe_load(f)

