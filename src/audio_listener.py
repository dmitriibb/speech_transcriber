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
        self.listen_thread = None
        
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
                        
        self.listen_thread = Thread(target=self._process_audio)
        self.listen_thread.start()

    def _process_audio(self):
        with sd.InputStream(
                device=self.device,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=int(self.sample_rate * self.chunk_duration),
                callback=self._audio_callback
        ) as stream:
            self.stream = stream
            while not self.stop_event.is_set():
                try:
                    audio_chunk = self.audio_queue.get(timeout=1.0)
                    self.transcriber.transcribe_async(audio_chunk)
                    self.audio_queue.task_done()
                except Empty:
                    continue  # No chunks to process, continue waiting
        
    def stop(self):
        self.stop_event.set()
        self._stop_listening()

    def _stop_listening(self):
        if self.stream is not None:
            try:
                self.stream.stop()
            except Exception as ex:
                print(f"error - can't stop audio stream input: {ex}")

        if self.listen_thread is not None:
            self.listen_thread.join()
            self.listen_thread = None

        # send remaining audio chunks
        while not self.audio_queue.empty():
            audio_chunk = self.audio_queue.get()
            self.transcriber.transcribe_async(audio_chunk)
            self.audio_queue.task_done()
        self.transcriber.stop()