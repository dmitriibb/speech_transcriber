from src.constants import deviceTypeInput, deviceTypeOutput


class AudioDeviceWrapper:
    def __init__(self, device):
        self.device = device
        if device['max_input_channels'] > 0:
            self.type = deviceTypeInput
        else:
            self.type = deviceTypeOutput

    def get_name(self) -> str:
        return f"{self.type} - {self.device['name']}"