import sounddevice as sd
import numpy as np
from queue import Queue
from threading import Thread, Event

from src.transcriber import Transcriber


class AudioListener:
    def __init__(self, chunk_duration=5):
        """
        Initialize the AudioListener.
        
        Args:
            chunk_duration (int): Duration of each audio chunk in seconds
        """
        self.chunk_duration = chunk_duration
        self.device = None
        self.stream = None
        self.stop_event = Event()
        self.audio_queue = Queue()
        self.sample_rate = 16000  # Standard sample rate for speech
        
    def set_input_device(self, device_name):
        """Set the input device by name."""
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev['name'] == device_name and dev['max_input_channels'] > 0:
                self.device = i
                break
                
    def _audio_callback(self, indata, frames, time, status):
        """Callback function for the audio stream."""
        if status:
            print(f'Audio callback status: {status}')
        if not self.stop_event.is_set():
            self.audio_queue.put(indata.copy())
            
    def start(self, transcriber: Transcriber):
        if self.device is None:
            raise ValueError("Input device not set")
            
        self.stop_event.clear()
        
        def process_audio():
            with sd.InputStream(
                device=self.device,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=int(self.sample_rate * self.chunk_duration),
                callback=self._audio_callback
            ):
                while not self.stop_event.is_set():
                    if not self.audio_queue.empty():
                        audio_chunk = self.audio_queue.get()
                        transcriber.transcribe_async(audio_chunk)
                transcriber.stop()
                        
        self.listen_thread = Thread(target=process_audio)
        self.listen_thread.start()
        
    def stop(self):
        """Stop listening to the audio input."""
        self.stop_event.set()
        if hasattr(self, 'listen_thread'):
            self.listen_thread.join()
        # Clear the queue
        while not self.audio_queue.empty():
            self.audio_queue.get() 