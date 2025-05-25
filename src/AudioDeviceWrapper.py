from src.constants import deviceTypeInput, deviceTypeOutput


class AudioDeviceWrapper:
    def __init__(self, device):
        self.device_info = device
        self.device_id = device['index']  # Use the device index for sounddevice
        if device['max_input_channels'] > 0:
            self.type = deviceTypeInput
        else:
            self.type = deviceTypeOutput

    def get_name(self) -> str:
        return f"{self.type} - {self.device_info['name']}"

    @property
    def device(self):
        return self.device_id  # Return just the device index for sounddevice