# fsm/fsm.py

class FakeFSM:
    """A minimal stub for the FSM object."""
    def __init__(self):
        print("[FSM] Stub FSM initialized")

    def connect(self, signal_name, callback):
        """Stub connect function for signals."""
        print(f"[FSM] Connected signal: {signal_name}")

def main():
    """Return a stub FSM object for testing."""
    return FakeFSM()
    