
class OutputConfig:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

class AudioListenerConfig:
    def __init__(self, audio_device_name: str, chunk_duration: int):
        self.audio_device_name = audio_device_name
        self.chunk_duration = chunk_duration

class TranscriberConfig:
    def __init__(self, recogniser_name: str):
        self.recogniser_name = recogniser_name