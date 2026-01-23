import uasyncio as asyncio
from proto import send_msg, serial_rx_task
from state import SimState
from commands import CommandDispatcher
from sim import sim_tick_task, sensor_stream_task

async def main():
    state = SimState()
    dispatcher = CommandDispatcher(state)

    send_msg({
        "type": "hello",
        "fw": "micropython-sim",
        "proto": 1,
        "device": "pico",
        "features": dispatcher.features(),
    })

    asyncio.create_task(sim_tick_task(state, tick_hz=100.0))
    asyncio.create_task(sensor_stream_task(state, tick_hz=100.0))

    await serial_rx_task(dispatcher)

try:
    asyncio.run(main())
finally:
    try:
        asyncio.new_event_loop()
    except Exception:
        pass
