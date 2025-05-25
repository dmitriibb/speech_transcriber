import sounddevice as sd

from src.AudioDeviceWrapper import AudioDeviceWrapper


def get_devices_names():
    devices = sd.query_devices()
    names = []
    for device in devices:
        wrapper = AudioDeviceWrapper(device)
        names.append(wrapper.get_name())
    return names

def get_device_by_name(name: str) -> AudioDeviceWrapper:
    devices = sd.query_devices()
    for device in devices:
        wrapper = AudioDeviceWrapper(device)
        if wrapper.get_name() == name:
            return wrapper
    raise Exception(f"can't find audio device {name}")