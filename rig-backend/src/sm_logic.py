import can
import time
import threading
import sys
import select

# -------------------------
# CAN setup (single bus)
# -------------------------
bus = can.interface.Bus(channel='vcan0', interface='socketcan', receive_own_messages=True)

# -------------------------
# IDs
# -------------------------
ID_CANISTER_INSERT = 0x4C
ID_OPEN_VALVES     = 0x60
ID_UPDATE_VOLUME   = 0x34
ID_CLOSE_VALVES    = 0x62

TARGET_VOLUME = 1000
STEP_VOLUME   = 100
STEP_TIME     = 0.3

running = True


def clean_id(msg):
    return msg.arbitration_id & 0x1FFFFFFF


# -------------------------
# Hardware Emulator
# -------------------------
def hardware_emulator_thread():
    print("[EMU] Emulator online")

    dispensing = False
    volume = 0

    while running:
        msg = bus.recv(timeout=0.05)

        if msg:
            cid = clean_id(msg)

            if cid == ID_OPEN_VALVES:
                print("[EMU] Valves opened")
                dispensing = True
                volume = 0

            elif cid == ID_CLOSE_VALVES:
                print("[EMU] Valves closed")
                dispensing = False

        if dispensing:
            time.sleep(STEP_TIME)

            volume = min(volume + STEP_VOLUME, TARGET_VOLUME)

            data = volume.to_bytes(4, 'big') + b'\x00' * 4
            bus.send(can.Message(
                arbitration_id=ID_UPDATE_VOLUME,
                data=data,
                is_extended_id=True
            ))

            print(f"[EMU] Sent volume: {volume} ml")

            if volume >= TARGET_VOLUME:
                dispensing = False
                print("[EMU] Target reached, auto-stopping")


# -------------------------
# System Manager
# -------------------------
def system_manager_thread():
    print("[SM] System Manager online")

    while running:
        msg = bus.recv(timeout=0.2)
        if not msg:
            continue

        cid = clean_id(msg)

        if cid == ID_UPDATE_VOLUME:
            vol = int.from_bytes(msg.data[0:4], 'big')
            print(f"[SM] >>> Dispensed: {vol} ml")

            if vol >= TARGET_VOLUME:
                print("[SM] Target achieved, closing valves")
                bus.send(can.Message(
                    arbitration_id=ID_CLOSE_VALVES,
                    is_extended_id=True
                ))


# -------------------------
# Keyboard Controller
# -------------------------
def keyboard_thread():
    global running
    print("\nControls:")
    print("  d = Dock canister")
    print("  s = Start dispensing")
    print("  u = Undock / stop")
    print("  q = Quit\n")

    while running:
        if select.select([sys.stdin], [], [], 0.1)[0]:
            key = sys.stdin.readline().strip().lower()

            if key == "d":
                print("[UI] Docking canister")
                bus.send(can.Message(
                    arbitration_id=ID_CANISTER_INSERT,
                    is_extended_id=True
                ))

            elif key == "s":
                print("[UI] Starting dispense")
                bus.send(can.Message(
                    arbitration_id=ID_OPEN_VALVES,
                    is_extended_id=True
                ))

            elif key == "u":
                print("[UI] Manual stop")
                bus.send(can.Message(
                    arbitration_id=ID_CLOSE_VALVES,
                    is_extended_id=True
                ))

            elif key == "q":
                print("[UI] Exiting")
                running = False
                break


# -------------------------
# Main
# -------------------------
if __name__ == "__main__":
    threads = [
        threading.Thread(target=hardware_emulator_thread, daemon=True),
        threading.Thread(target=system_manager_thread, daemon=True),
        threading.Thread(target=keyboard_thread)
    ]

    for t in threads:
        t.start()

    try:
        threads[-1].join()
    finally:
        running = False
        print("\nSystem shutdown complete")
