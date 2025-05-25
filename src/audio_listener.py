import sounddevice as sd
import numpy as np
from queue import Queue, Empty
from threading import Thread, Event

from src.transcriber import Transcriber


class AudioListener:
    def __init__(self, transcriber: Transcriber, chunk_duration=5):
        self.transcriber = transcriber
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
            
    def start(self):
        if self.device is None:
            raise ValueError("Input device not set")

        if self.transcriber is None:
            raise ValueError("Transcriber not set")
            
        self.stop_event.clear()
        
        # TO REFACTOR - move this function outside of the method.
        def process_audio():
            with sd.InputStream(
                device=self.device,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=int(self.sample_rate * self.chunk_duration),
                callback=self._audio_callback
            ):
                while not self.stop_event.is_set():
                    try:
                        audio_chunk = self.audio_queue.get(timeout=1.0)
                        self.transcriber.transcribe_async(audio_chunk)
                        self.audio_queue.task_done()
                    except Empty:
                        continue  # No chunks to process, continue waiting
                        
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

    def _stop_listening(self):
        # TO REFACTOR - need to stop listening self.device InputStream
        while not self.audio_queue.empty():
            audio_chunk = self.audio_queue.get()
            self.transcriber.transcribe_async(audio_chunk)
            self.audio_queue.task_done()
        self.transcriber.stop()