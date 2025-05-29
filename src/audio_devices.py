from threading import Thread

import sounddevice as sd

from src.AudioDeviceWrapper import AudioDeviceWrapper


def get_devices_names(include_output_devices = False):
    devices = sd.query_devices()
    names = []
    for device in devices:
        if device['max_input_channels'] == 0 and not include_output_devices:
            continue
        wrapper = AudioDeviceWrapper(device)
        names.append(wrapper.get_name())
    return names

def get_device_by_name(name: str) -> AudioDeviceWrapper:
    devices = sd.query_devices()
    for device in devices:
        if device['max_input_channels'] == 0:
            continue
        wrapper = AudioDeviceWrapper(device)
        if wrapper.get_name() == name:
            return wrapper
    raise Exception(f"can't find audio device {name}")

# Below is attempt to record sound from output audio device. Unfortunately it didn't work in Windows
def find_loopback_device():
    devices = sd.query_devices()
    for idx, device in enumerate(devices):
        if device['hostapi'] == sd.default.hostapi and device['name'].lower().find('loopback') != -1:
            return idx
    raise RuntimeError("No loopback device found. Use a WASAPI-compatible sound card on Windows.")

class SystemSoundRecorder:
    def __init__(self, device_id, channels, samplerate, blocksize, duration, callback):
        self.device_id = device_id
        self.channels = channels
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.duration = duration
        self.callback = callback

        self._start_processing_thread()

    def _start_processing_thread(self):
        """Start the background thread for processing audio chunks."""
        self._should_stop = False
        self._processing_thread = Thread(target=self._recording(), daemon=True)
        self._processing_thread.start()

    def _recording(self):
        # Get loopback input device
        # device = find_loopback_device()

        # Record
        print("Recording...")
        # while not self._should_stop:
            # recording = sd.rec(int(self.duration * self.samplerate), samplerate=self.samplerate,channels=2, device=self.device_id, blocking=True)
            # recording = sd.rec(int(self.duration * self.samplerate), samplerate=self.samplerate, channels=2, device=self.device_id, dtype='float32')
            # sd.wait()
            # self.callback(recording, None, None, None)

        try:
            with sd.InputStream(device=self.device_id,
                                channels=self.channels,
                                samplerate=self.samplerate,
                                blocksize=self.blocksize,
                                callback=self.callback) as stream:
                while not self._should_stop:
                    sd.sleep(100)  # Sleep to prevent busy waiting
        except Exception as e:
            print(f"Error in system sound recording: {e}")

        # print("Recording complete.")

    def stop(self):
        self._should_stop = True
