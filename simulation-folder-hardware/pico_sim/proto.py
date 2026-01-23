import ujson as json
import sys
import uasyncio as asyncio
import uselect

def send_msg(msg):
    # newline-delimited JSON
    sys.stdout.write(json.dumps(msg) + "\n")
    try:
        sys.stdout.flush()
    except Exception:
        pass

async def serial_rx_task(dispatcher):
    poller = uselect.poll()
    poller.register(sys.stdin, uselect.POLLIN)

    while True:
        ev = poller.poll(0)
        if not ev:
            await asyncio.sleep_ms(10)
            continue

        line = sys.stdin.readline()
        if not line:
            await asyncio.sleep_ms(10)
            continue

        try:
            msg = json.loads(line)
        except Exception:
            continue

        if not isinstance(msg, dict):
            continue

        if msg.get("type") != "cmd":
            continue

        cid = msg.get("id")
        name = msg.get("name", "")
        args = msg.get("args", {})

        if not isinstance(cid, int):
            continue
        if not isinstance(args, dict):
            args = {}

        await dispatcher.handle_cmd(cid, name, args)
