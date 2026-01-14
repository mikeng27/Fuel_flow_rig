import sys
import os
import random
import time
import threading

# Ensure the 'src' directory is in the path so we can import local modules
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)


from fdm import fdm
from fsm import fsm
from pm import pm
from heartbeat.send_heartbeat import send_heartbeat
from config_loader import load_config

# 1. Load YAML once here at the top level
io_config = load_config()

def generate_random_value(config_entry):
    if "min" in config_entry and "max" in config_entry:
        return round(random.uniform(config_entry["min"], config_entry["max"]), 2)
    return None

# 2. Pass the io_config into the sub-modules
fsm_obj = fsm.main()
fdm_emulator = fdm.main(fsm_obj=fsm_obj, io_config=io_config) 
pm.main()

def send_yaml_heartbeat():
    send_heartbeat()

def heartbeat_loop():
    while True:
        send_yaml_heartbeat()
        time.sleep(60)

# Run heartbeat in a separate thread
threading.Thread(target=heartbeat_loop, daemon=True).start()

try:
    while True:
        send_yaml_heartbeat()  # send heartbeat every minute
        time.sleep(60)         # wait 60 seconds
except KeyboardInterrupt:
    print("Exiting simulation...")