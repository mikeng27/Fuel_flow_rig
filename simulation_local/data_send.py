# data_send.py
import json
import threading
import time
import pika
from influxdb_client import InfluxDBClient, Point, WriteOptions

# ======================
# CONFIG
# ======================
RABBIT_HOST = "localhost"
RABBIT_USER = "admin"
RABBIT_PASS = "mypassword"
HEARTBEAT_QUEUE = "heartbeat_queue"
EVENT_QUEUE = "event_queue"

INFLUX_URL = "http://localhost:8086"
INFLUX_TOKEN = "uNxYDfsNHBTz8XLLnTqm956w5ccWi2y_P-zeFuIEfwysDW1UErNKJ_HIhXqvYlDadlxYk8JUnfbaBBsk7kzEJw=="  # replace with your token
INFLUX_ORG = "KOKO"
INFLUX_BUCKET = "KP_fuel_flow_rig"

# ======================
# InfluxDB Client (v2)
# ======================
influx_client = InfluxDBClient(
    url=INFLUX_URL,
    token=INFLUX_TOKEN,
    org=INFLUX_ORG
)

write_api = influx_client.write_api(write_options=WriteOptions(batch_size=1))

# ======================
# Functional Processing
# ======================
def process_heartbeat(msg: dict):
    """
    Convert heartbeat message to InfluxDB Point and write.
    Properly handles numeric and boolean fields to avoid 422 errors.
    """
    try:
        p = Point("heartbeat").time(int(msg["Timestamp"] * 1e9))  # nanoseconds
        # Add numeric fields
        for field in ["canister_mass", "sump_mass", "pump_voltage", "pump_current",
                      "dv_voltage", "dv_current"]:
            p = p.field(field, float(msg.get(field, 0)))
        # Convert booleans to int
        p = p.field("ev1_status", int(msg.get("ev1_status", False)))
        p = p.field("ev2_status", int(msg.get("ev2_status", False)))

        write_api.write(bucket=INFLUX_BUCKET, record=p)
        print("[HB -> Influx written]", msg["Timestamp"], "fields:", len(p.to_line_protocol().split(",")) - 1)
    except Exception as e:
        print("[HB ERROR]", e, msg)


def process_event(msg: dict):
    """
    Convert event message to InfluxDB Point and write.
    Handles numeric, boolean, and string fields correctly.
    """
    try:
        event_name = msg.get("event", "unknown")
        ts = msg.get("ts", time.time())
        p = Point("event").tag("event", event_name).time(int(ts * 1e9))

        for k, v in msg.get("data", {}).items():
            if isinstance(v, (int, float)):
                p = p.field(k, v)
            elif isinstance(v, bool):
                p = p.field(k, int(v))
            else:
                p = p.field(k, str(v))

        write_api.write(bucket=INFLUX_BUCKET, record=p)
        print("[EVENT -> Influx written]", event_name)
    except Exception as e:
        print("[EVENT ERROR]", e, msg)

# ======================
# RabbitMQ Consumers
# ======================
def start_heartbeat_consumer():
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue=HEARTBEAT_QUEUE, durable=True)

    def callback(ch, method, properties, body):
        msg = json.loads(body)
        process_heartbeat(msg)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=HEARTBEAT_QUEUE, on_message_callback=callback)
    print("[HEARTBEAT CONSUMER] Waiting for messages...")
    channel.start_consuming()


def start_event_consumer():
    credentials = pika.PlainCredentials(RABBIT_USER, RABBIT_PASS)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue=EVENT_QUEUE, durable=True)

    def callback(ch, method, properties, body):
        msg = json.loads(body)
        process_event(msg)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=EVENT_QUEUE, on_message_callback=callback)
    print("[EVENT CONSUMER] Waiting for messages...")
    channel.start_consuming()

# ======================
# Main: Run both consumers concurrently
# ======================
def main():
    hb_thread = threading.Thread(target=start_heartbeat_consumer, daemon=True)
    ev_thread = threading.Thread(target=start_event_consumer, daemon=True)

    hb_thread.start()
    ev_thread.start()

    print("[DATA_SEND] Both consumers running...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[DATA_SEND] Exiting...")
        # Properly close Influx client
        write_api.__del__()
        influx_client.__del__()

if __name__ == "__main__":
    main()

