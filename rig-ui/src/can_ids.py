# Base CAN classes
class CANMessageError(Exception): pass
class CANId: pass
class CANMessagePayload: pass
class CANMessage: pass

from enum import IntEnum

class Priority(IntEnum):
    CRITICAL = 0
    REALTIME = 1

class Destination(IntEnum):
    PUMP_1 = 0
    PUMP_2 = 1
    MOTORIZED_BALL_VALVE_1 = 2
    SOLENOID_VALVE_1 = 3
    SOLENOID_VALVE_2 = 4
    DISPENSE_VALVE = 5
    CANISTER_DOCK_SWITCH = 6
    SYSTEM_MANAGER = 7
    POWER_MODULE = 8

class Source(IntEnum):
    SYSTEM_MANAGER = 0
    FUEL_DISPENSE = 1
    POWER_MODULE = 2

class MessageID(IntEnum):
    FLOW_RETURN = 1
    FLOW_DISPENSE_COLUMN_1 = 2
    FLOW_DISPENSE_COLUMN_2 = 3
    PRESSURE_SENSOR_1 = 4
    PRESSURE_SENSOR_2 = 5
    TEMP_SENSOR_1 = 6
    TEMP_SENSOR_2 = 7
    TEMP_SENSOR_3 = 8
    LEVEL_SENSOR_1 = 9
    LOAD_CELL_1 = 10
    LOAD_CELL_2 = 11
    ULTRASONIC_LEVEL_SENSOR_1 = 12
    CURRENT_SENSOR_1 = 13
    CURRENT_SENSOR_2 = 14
    CURRENT_SENSOR_3 = 15
    VOLTAGE_SENSOR_1 = 16
    VOLTAGE_SENSOR_2 = 17
    VOLTAGE_SENSOR_3 = 18

# Event payload classes
class EventPump1(CANMessagePayload):
    flow: float
    pressure: float

class EventPump2(CANMessagePayload):
    flow: float
    pressure: float

class EventMotorizedBallValve1(CANMessagePayload):
    state: bool

class EventSolenoidValve1(CANMessagePayload):
    state: bool

class EventSolenoidValve2(CANMessagePayload):
    state: bool

class EventDispenseValve(CANMessagePayload):
    state: bool

class EventCanisterDockSwitch(CANMessagePayload):
    state: bool

class EventFlowReturn(CANMessagePayload):
    value: float

class EventFlowDispenseColumn1(CANMessagePayload):
    value: float

class EventFlowDispenseColumn2(CANMessagePayload):
    value: float

class EventPressureSensor1(CANMessagePayload):
    value: float

class EventPressureSensor2(CANMessagePayload):
    value: float

class EventTempSensor1(CANMessagePayload):
    value: float

class EventTempSensor2(CANMessagePayload):
    value: float

class EventTempSensor3(CANMessagePayload):
    value: float

class EventLevelSensor1(CANMessagePayload):
    value: float

class EventLoadCell1(CANMessagePayload):
    value: float

class EventLoadCell2(CANMessagePayload):
    value: float

class EventUltrasonicLevelSensor1(CANMessagePayload):
    value: float

class EventCurrentSensor1(CANMessagePayload):
    value: float

class EventCurrentSensor2(CANMessagePayload):
    value: float

class EventCurrentSensor3(CANMessagePayload):
    value: float

class EventVoltageSensor1(CANMessagePayload):
    value: float

class EventVoltageSensor2(CANMessagePayload):
    value: float

class EventVoltageSensor3(CANMessagePayload):
    value: float

class EventBatteryPower(CANMessagePayload):
    voltage: float
    current: float
    status: int

class EventPowerManagementModule(CANMessagePayload):
    voltage: float
    current: float
    status: int

class EventSystem_manager(CANMessagePayload):
    pass

class EventPower_module(CANMessagePayload):
    pass

