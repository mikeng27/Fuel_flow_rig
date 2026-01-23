import time
import can

ID_UPDATE_VOLUME = 0x34

def main(channel="vcan0", target_ml=1000, step_ml=50, period_s=0.2):
    bus = can.interface.Bus(channel=channel, interface="socketcan", receive_own_messages=True)
    vol = 0
    try:
        while vol < target_ml:
            vol += step_ml
            data = vol.to_bytes(4, "big") + b"\x00\x00\x00\x00"
            msg = can.Message(arbitration_id=ID_UPDATE_VOLUME, is_extended_id=True, data=data)
            bus.send(msg)
            print(f"[SIM] sent volume={vol} ml")
            time.sleep(period_s)
        print("[SIM] done")
    finally:
        bus.shutdown()

if __name__ == "__main__":
    main()
