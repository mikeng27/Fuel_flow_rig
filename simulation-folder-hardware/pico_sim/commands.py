import time
from proto import send_msg
from faults import add_fault, clear_faults, set_scenario

class CommandDispatcher:
    def __init__(self, state):
        self.s = state

    def features(self):
        return [
            "heartbeat", "safe_stop",
            "start_stream", "stop_stream", "snapshot",
            "drain_canister_to_sump", "drain_sump_to_tank",
            "set_fault", "clear_faults",
            "reset_sim", "set_deterministic", "set_scenario",
        ]

    def _ok(self, cid, result=None):
        send_msg({"type": "cmd_result", "id": cid, "ok": True, "result": result or {}})

    def _err(self, cid, err):
        send_msg({"type": "cmd_result", "id": cid, "ok": False, "error": str(err)})

    def _start_job(self, job):
        if self.s.job is not None:
            self._err(job["cid"], "busy: job already running")
            return
        self.s.job = job
        self.s._stable_start_ms = None

    def _reset_sim(self):
        self.s.canister_mass_kg = 1.50
        self.s.sump_mass_kg = 0.20
        self.s.tank1_mass_kg = 5.00
        self.s.tank2_mass_kg = 5.00

        self.s.bus_voltage_v = 24.0
        self.s.pump_pressure_bar = 1.0
        self.s.pump_current_a = 1.0
        self.s.dv_current_a = 0.2

        self.s.stream_enabled = False
        self.s.stream_hz = 10.0
        self.s.stream_pause_until_ms = 0

        self.s.sim_tick = 0
        self.s.job = None
        self.s._stable_start_ms = None

        self.s.faults = []
        set_scenario(self.s, "none")

    async def handle_cmd(self, cid, name, args):
        try:
            if name == "heartbeat":
                self._ok(cid, {"ts_ms": time.ticks_ms()})

            elif name == "safe_stop":
                self.s.job = None
                self.s.stream_enabled = False
                self.s.pump_pressure_bar = 1.0
                self.s.bus_voltage_v = 24.0
                self.s.pump_current_a = 1.0
                self.s.dv_current_a = 0.2
                self._ok(cid, {"stopped": True})

            elif name == "start_stream":
                hz = float(args.get("hz", 10.0))
                self.s.stream_hz = max(0.2, min(50.0, hz))
                self.s.stream_enabled = True
                self._ok(cid, {"stream": "on", "hz": self.s.stream_hz})

            elif name == "stop_stream":
                self.s.stream_enabled = False
                self._ok(cid, {"stream": "off"})

            elif name == "snapshot":
                self._ok(cid, self.s.sensors_dict())

            elif name == "drain_canister_to_sump":
                ev = str(args.get("ev", "ev1"))
                timeout_s = float(args.get("timeout_s", 60.0))
                stable_eps_kg = float(args.get("stable_eps_kg", 0.01))
                stable_time_s = float(args.get("stable_time_s", 2.0))
                self._start_job({
                    "type": "drain_canister_to_sump",
                    "cid": cid,
                    "ev": ev,
                    "timeout_ms": int(timeout_s * 1000),
                    "stable_eps_kg": stable_eps_kg,
                    "stable_time_ms": int(stable_time_s * 1000),
                    "started_ms": time.ticks_ms(),
                    "moved_kg": 0.0,
                })

            elif name == "drain_sump_to_tank":
                tank = str(args.get("tank", "TANK2"))
                timeout_s = float(args.get("timeout_s", 120.0))
                sump_empty_kg = float(args.get("sump_empty_kg", 0.05))
                stable_eps_kg = float(args.get("stable_eps_kg", 0.01))
                stable_time_s = float(args.get("stable_time_s", 2.0))
                self._start_job({
                    "type": "drain_sump_to_tank",
                    "cid": cid,
                    "tank": tank,
                    "timeout_ms": int(timeout_s * 1000),
                    "sump_empty_kg": sump_empty_kg,
                    "stable_eps_kg": stable_eps_kg,
                    "stable_time_ms": int(stable_time_s * 1000),
                    "started_ms": time.ticks_ms(),
                    "moved_kg": 0.0,
                })

            # (Optional later) manual fault injection
            elif name == "set_fault":
                ftype = str(args.get("type", "pressure_high"))
                duration_s = float(args.get("duration_s", 3.0))
                value = args.get("value", None)
                add_fault(self.s, ftype, duration_s, value)
                self._ok(cid, {"fault": ftype, "duration_s": duration_s, "value": value})

            elif name == "clear_faults":
                clear_faults(self.s)
                self._ok(cid, {"cleared": True})

            elif name == "reset_sim":
                self._reset_sim()
                self._ok(cid, {"reset": True})

            elif name == "set_deterministic":
                self.s.deterministic = bool(args.get("enabled", True))
                self._ok(cid, {"deterministic": self.s.deterministic})

            elif name == "set_scenario":
                scen = str(args.get("name", "none"))
                set_scenario(self.s, scen)
                self._ok(cid, {"scenario": self.s.scenario_name})

            else:
                self._err(cid, "unknown command: " + str(name))

        except Exception as e:
            self._err(cid, e)
