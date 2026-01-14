import queue
import threading
import time
from typing import Dict, List, Any
from generate import python_header as can_defs  # your generated CAN classes

class VirtualCANBus:
    """
    A simple in-memory CAN bus simulator.
    """
    def __init__(self):
        self._bus = queue.Queue()  # virtual bus
        self._lock = threading.Lock()
        self._listeners: List[callable] = []

    def send(self, msg: "can_defs.CANMessage"):
        """Send a CAN message onto the virtual bus."""
        with self._lock:
            print(f"➡️ Sending CAN ID 0x{msg.can_id:03X} data={msg.payload_bytes}")
            self._bus.put(msg)
            # Notify listeners
            for callback in self._listeners:
                callback(msg)

    def recv(self, timeout: float = 1.0) -> "can_defs.CANMessage | None":
        """Receive a message from the virtual bus."""
        try:
            msg = self._bus.get(timeout=timeout)
            print(f"⬅️ Received CAN ID 0x{msg.can_id:03X} data={msg.payload_bytes}")
            return msg
        except queue.Empty:
            return None

    def add_listener(self, callback: callable):
        """
        Register a listener function(msg) that is called whenever a message is sent.
        """
        self._listeners.append(callback)


# ------------------------------
# Optional: example usage
# ------------------------------
if __name__ == "__main__":
    # Import your generated CAN classes
    from generate.python_header import CANMessage, CANMessagePayload, MessageID, Priority, Destination

    # Dummy payload class
    class ConfigSettings(CANMessagePayload):
        version: int
        _struct_format: str = "<"

    bus = VirtualCANBus()

    # Send a message
    payload = ConfigSettings()
    payload.version = 42

    msg = CANMessage()  # fill the required attributes
    msg.can_id = 0x01
    msg.payload_bytes = b"\x2A\x00\x00\x00"  # 42 as 4 bytes

    bus.send(msg)

    # Receive it
    received = bus.recv()
    print(f"Simulator received message: CAN ID={received.can_id}, payload={received.payload_bytes}")
