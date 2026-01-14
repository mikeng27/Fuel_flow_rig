# Auto-generated Python CAN ID definitions

from enum import IntEnum

class Priority(IntEnum):
    CRITICAL = 0b00
    REALTIME = 0b01

class Destination(IntEnum):
    PUMP_1 = 0b00
    PUMP_2 = 0b01
    MOTORIZED_BALL_VALVE_1 = 0b10
    SOLENOID_VALVE_1 = 0b11
    SOLENOID_VALVE_2 = 0b100
    DISPENSE_VALVE = 0b101
    CANISTER_DOCK_SWITCH = 0b110

class Source(IntEnum):
    SYSTEM_MANAGER = 0b00
    FUEL_DISPENSE = 0b01

class MessageID(IntEnum):
    FLOW_RETURN = 0b000000000000000000001
    FLOW_DISPENSE_COLUMN_1 = 0b000000000000000000010
    FLOW_DISPENSE_COLUMN_2 = 0b000000000000000000011
    PRESSURE_SENSOR_1 = 0b000000000000000000100
    PRESSURE_SENSOR_2 = 0b000000000000000000101
    TEMP_SENSOR_1 = 0b000000000000000000110
    TEMP_SENSOR_2 = 0b000000000000000000111
    TEMP_SENSOR_3 = 0b000000000000000001000
    LEVEL_SENSOR_1 = 0b000000000000000001001
    LOAD_CELL_1 = 0b000000000000000001010
    LOAD_CELL_2 = 0b000000000000000001011
    ULTRASONIC_LEVEL_SENSOR_1 = 0b000000000000000001100
    CURRENT_SENSOR_1 = 0b000000000000000001101
    CURRENT_SENSOR_2 = 0b000000000000000001110
    CURRENT_SENSOR_3 = 0b000000000000000001111
    VOLTAGE_SENSOR_1 = 0b000000000000000010000
    VOLTAGE_SENSOR_2 = 0b000000000000000010001
    VOLTAGE_SENSOR_3 = 0b000000000000000010010

class FlowReturn(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class FlowDispenseColumn1(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class FlowDispenseColumn2(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class PressureSensor1(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class PressureSensor2(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class TempSensor1(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class TempSensor2(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class TempSensor3(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class LevelSensor1(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class LoadCell1(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class LoadCell2(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class UltrasonicLevelSensor1(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class CurrentSensor1(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class CurrentSensor2(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class CurrentSensor3(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class VoltageSensor1(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class VoltageSensor2(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed

class VoltageSensor3(CANMessagePayload):
    value: float
    _struct_format: str = '<'  # adjust as needed



class CANMessageError(Exception): pass


class CANId: pass


class CANMessagePayload: pass


class CANMessage: pass
