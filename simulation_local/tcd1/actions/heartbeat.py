async def heartbeat(ctrl):
    return await ctrl.call("heartbeat", {}, 2.0)