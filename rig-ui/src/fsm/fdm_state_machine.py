# Dummy FDMStateMachine stub for testing

class FDMStateMachine:
    def __init__(self):
        self._callbacks = {"dispense_started": [],
                           "dispense_updated": [],
                           "dispense_stopped": []}

    def connect(self, signal, callback):
        if signal in self._callbacks:
            self._callbacks[signal].append(callback)

    # Fake signals for testing
    def trigger_dispense_started(self, volume):
        for cb in self._callbacks["dispense_started"]:
            cb(self, volume)

    def trigger_dispense_updated(self, volume):
        for cb in self._callbacks["dispense_updated"]:
            cb(self, volume)

    def trigger_dispense_stopped(self):
        for cb in self._callbacks["dispense_stopped"]:
            cb(self)
