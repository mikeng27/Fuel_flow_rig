# rig-ui/src/heartbeat/send_heartbeat.py
from random import randint, choice
from can_ids import (
    CANMessage,
    CANMessagePayload,
    Priority,
    Destination,
    Source,
    EventPump1,
    EventPump2,
    EventMotorizedBallValve1,
    EventSolenoidValve1,
    EventSolenoidValve2,
    EventDispenseValve,
    EventCanisterDockSwitch,
    EventFlowReturn,
    EventFlowDispenseColumn1,
    EventFlowDispenseColumn2,
    EventPressureSensor1,
    EventPressureSensor2,
    EventTempSensor1,
    EventTempSensor2,
    EventTempSensor3,
    EventLevelSensor1,
    EventLoadCell1,
    EventLoadCell2,
    EventUltrasonicLevelSensor1,
    EventCurrentSensor1,
    EventCurrentSensor2,
    EventCurrentSensor3,
    EventVoltageSensor1,
    EventVoltageSensor2,
    EventVoltageSensor3,
    EventPowerManagementModule,
    EventBatteryPower
)
import time
import threading

# -------------------------------
# Thread-safe print lock
# -------------------------------
print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)

# -------------------------------
# Mock CAN interface
# -------------------------------
class MockCANInterface:
    def send(self, msg: CANMessage):
        # Print readable message
        payload_fields = ", ".join(f"{k}={getattr(msg.payload, k)}" 
                                   for k in vars(msg.payload) if not k.startswith("__"))
        safe_print(f"[CAN SEND] {msg.source.name} -> {msg.destination.name} | "
                   f"{msg.payload.__class__.__name__}({payload_fields})")

can_interface = MockCANInterface()

# -------------------------------
# Helper to send an event
# -------------------------------
def send_event(event_cls, payload: dict, source: Source, destination: Destination):
    # Create event instance
    event = event_cls()
    for k, v in payload.items():
        setattr(event, k, v)

    # Wrap in CANMessage
    msg = CANMessage()
    msg.payload = event
    msg.priority = Priority.REALTIME
    msg.source = source
    msg.destination = destination

    # Send
    can_interface.send(msg)

# -------------------------------
# Heartbeat simulation
# -------------------------------
def send_heartbeat():
    safe_print("[HEARTBEAT] Sending CAN heartbeat...")

    source_fsm = Source.SYSTEM_MANAGER
    source_fdm = Source.FUEL_DISPENSE
    source_pm = Source.POWER_MODULE

    # Actuators
    send_event(EventPump1, {"flow": round(randint(0, 27)/10, 2), "pressure": round(randint(0, 380), 2)},
               source_fdm, Destination.PUMP_1)
    send_event(EventPump2, {"flow": round(randint(0, 120)/10, 2), "pressure": round(randint(0, 300), 2)},
               source_fdm, Destination.PUMP_2)
    send_event(EventMotorizedBallValve1, {}, source_fdm, Destination.MOTORIZED_BALL_VALVE_1)
    send_event(EventSolenoidValve1, {"state": choice([True, False])}, source_fdm, Destination.SOLENOID_VALVE_1)
    send_event(EventSolenoidValve2, {"state": choice([True, False])}, source_fdm, Destination.SOLENOID_VALVE_2)
    send_event(EventDispenseValve, {"state": choice([True, False])}, source_fdm, Destination.DISPENSE_VALVE)
    send_event(EventCanisterDockSwitch, {"state": choice([True, False])}, source_fdm, Destination.CANISTER_DOCK_SWITCH)

    # Sensors
    send_event(EventFlowReturn, {"value": round(randint(5, 150)/10, 2)}, source_fdm, Destination.PUMP_1)
    send_event(EventFlowDispenseColumn1, {"value": round(randint(5, 150)/10, 2)}, source_fdm, Destination.PUMP_1)
    send_event(EventFlowDispenseColumn2, {"value": round(randint(5, 150)/10, 2)}, source_fdm, Destination.PUMP_2)
    send_event(EventPressureSensor1, {"value": round(randint(0, 125), 2)}, source_fdm, Destination.PUMP_1)
    send_event(EventPressureSensor2, {"pressure": round(randint(0, 10000)/10, 2),
                                       "temperature": round(randint(-20, 100)/1, 2)}, source_fdm, Destination.PUMP_2)
    send_event(EventTempSensor1, {"value": round(randint(-55, 125)/1, 2)}, source_fdm, Destination.PUMP_1)
    send_event(EventTempSensor2, {"value": round(randint(-50, 150)/1, 2)}, source_fdm, Destination.PUMP_2)
    send_event(EventTempSensor3, {"value": round(randint(-55, 75)/1, 2)}, source_fdm, Destination.PUMP_2)
    send_event(EventLevelSensor1, {"value": round(randint(0, 100)/1, 2)}, source_fdm, Destination.PUMP_1)
    send_event(EventLoadCell1, {"value": round(randint(0, 300)/1, 2)}, source_fdm, Destination.PUMP_1)
    send_event(EventLoadCell2, {"value": round(randint(0, 300)/1, 2)}, source_fdm, Destination.PUMP_2)
    send_event(EventUltrasonicLevelSensor1, {"value": round(randint(0, 5000)/1, 2)}, source_fdm, Destination.PUMP_1)
    send_event(EventCurrentSensor1, {"value": round(randint(-100, 100)/1, 2)}, source_pm, Destination.PUMP_1)
    send_event(EventCurrentSensor2, {"value": round(randint(-100, 100)/1, 2)}, source_pm, Destination.PUMP_2)
    send_event(EventCurrentSensor3, {"value": round(randint(-100, 100)/1, 2)}, source_pm, Destination.DISPENSE_VALVE)
    send_event(EventVoltageSensor1, {"value": round(randint(0, 500)/1, 2)}, source_pm, Destination.PUMP_1)
    send_event(EventVoltageSensor2, {"value": round(randint(0, 500)/1, 2)}, source_pm, Destination.PUMP_2)
    send_event(EventVoltageSensor3, {"value": round(randint(0, 500)/1, 2)}, source_pm, Destination.DISPENSE_VALVE)

    # Power management / battery
    send_event(EventBatteryPower, {"voltage": 12.8, "current": randint(1, 40), "status": 0},
               source_pm, Destination.PUMP_1)
    send_event(EventPowerManagementModule, {"voltage": 230, "current": randint(1, 20), "status": 0},
               source_pm, Destination.SYSTEM_MANAGER)

    safe_print("[HEARTBEAT] CAN heartbeat sent ✅\n")
