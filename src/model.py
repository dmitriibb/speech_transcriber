from enum import Enum
from dataclasses import dataclass
from typing import Optional

from constants import deviceTypeInput, deviceTypeOutput


class AudioDeviceWrapper:
    def __init__(self, device):
        self.device = device
        self.device_id = device['index']  # Use the device index for sounddevice
        if device['max_input_channels'] > 0:
            self.type = deviceTypeInput
        else:
            self.type = deviceTypeOutput

    def get_name(self) -> str:
        return f"{self.type}: {self.device['name']} ({self.device['hostapi']})"

class ChunkAudio:
    def __init__(self, index: int, data):
        self.index = index
        self.data = data

class ChunkTranscribed:
    def __init__(self, index: int, text: str, speaker_name: Optional[str] = None):
        self.index = index
        self.text = text
        self.speaker_name = speaker_name

class InputMode(Enum):
    LIVE = "Live"
    FILE = "File"

@dataclass
class AudioInputLine:
    device_name: str
    speaker_name: str
    record: bool
    transcribe: bool

class ListenerBase:
    def start(self):
        pass

    def stop(self):
        pass
