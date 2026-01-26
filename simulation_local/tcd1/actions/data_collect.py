async def start_stream(ctrl, hz: float = 10.0):
    return await ctrl.call("start_stream", {"hz": float(hz)}, 2.0)


async def stop_stream(ctrl):
    return await ctrl.call("stop_stream", {}, 2.0)


async def snapshot(ctrl):
    return await ctrl.call("snapshot", {}, 2.0)