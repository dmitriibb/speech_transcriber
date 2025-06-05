import sounddevice as sd
import numpy as np
from queue import Queue, Empty
from threading import Thread, Event

from src.model import AudioDeviceWrapper
from src.audio_devices import get_device_by_name, SystemSoundRecorder
from src.configs import AudioListenerConfig
from src.constants import deviceTypeInput
from src.logger import Logger, logger
from src.model import ChunkAudio
from src.transcriber import Transcriber


class AudioListener:
    def __init__(self, transcriber: Transcriber, config: AudioListenerConfig):
        self.transcriber = transcriber
        self.chunk_duration = config.chunk_duration
        self.device_wrapper = get_device_by_name(config.audio_device_name)
        self.stream = None
        self.stop_event = Event()
        self.audio_queue = Queue()
        self.sample_rate = 16000  # Standard sample rate for speech
        self.listen_thread = None
        self.chunk_counter = 0
            
    def start(self):
        if self.device_wrapper is None:
            raise ValueError("Input device not set")

        if self.transcriber is None:
            raise ValueError("Transcriber not set")
            
        self.stop_event.clear()
                        
        self.listen_thread = Thread(target=self._process_audio)
        self.listen_thread.start()
        logger.log(f"Start listening {self.device_wrapper.get_name()}")

    def _process_audio(self):
        if self.device_wrapper.type == deviceTypeInput:
            self._process_audio_input()
        else:
            self._process_audio_output()

    def _audio_callback(self, data, frames, time, status):
        """Callback function for the audio stream."""
        if status and self.app:
            logger.log(f'Audio callback status: {status}')
        if not self.stop_event.is_set():
            self.audio_queue.put(data.copy())

    def _process_audio_input(self):
        with sd.InputStream(
                device=self.device_wrapper.device_id,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=int(self.sample_rate * self.chunk_duration),
                callback=self._audio_callback
        ) as stream:
            self.stream = stream
            while not self.stop_event.is_set():
                try:
                    audio = self.audio_queue.get(timeout=1.0)
                    chunk = ChunkAudio(self.chunk_counter, audio)
                    self.transcriber.transcribe_async(chunk)
                    self.audio_queue.task_done()
                    self.chunk_counter += 1
                    logger.log(f"AudioListener chunk {self.chunk_counter}")
                except Empty:
                    continue  # No chunks to process, continue waiting

    def _process_audio_output(self):
        # This doesn't work
        with sd.OutputStream(
                device=self.device_wrapper.device_id,
                channels=2,
                samplerate=self.device_wrapper.device['default_samplerate'],
                blocksize=int(self.device_wrapper.device['default_samplerate'] * self.chunk_duration),
                callback=self._audio_callback
        ) as stream:
            self.stream = stream
            while not self.stop_event.is_set():
                try:
                    audio = self.audio_queue.get(timeout=1.0)
                    chunk = ChunkAudio(self.chunk_counter, audio)
                    self.transcriber.transcribe_async(chunk)
                    self.audio_queue.task_done()
                    self.chunk_counter += 1
                    logger.log(f"AudioListener chunk {self.chunk_counter}")
                except Empty:
                    continue  # No chunks to process, continue waiting
        # self.recorder = SystemSoundRecorder(
        #     self.device_wrapper.device_id,
        #     channels=2,
        #     samplerate=self.device_wrapper.device_info['default_samplerate'],
        #     blocksize=int(self.device_wrapper.device_info['default_samplerate'] * self.chunk_duration),
        #     duration=self.chunk_duration,
        #     callback=self._audio_callback
        # )
        
    def stop(self):
        self.stop_event.set()
        self._stop_listening()

    def _stop_listening(self):
        if self.stream is not None:
            try:
                self.stream.stop()
            except Exception as ex:
                logger.log(f"Error - can't stop audio stream input: {ex}")

        if hasattr(self, 'recorder'):
            if self.recorder is not None:
                try:
                    self.recorder.stop()
                except Exception as ex:
                    logger.log(f"Error - can't stop recording system output: {ex}")

        if self.listen_thread is not None:
            self.listen_thread.join()
            self.listen_thread = None

        # send remaining audio chunks
        while not self.audio_queue.empty():
            audio_chunk = self.audio_queue.get()
            self.transcriber.transcribe_async(audio_chunk)
            self.audio_queue.task_done()
        self.transcriber.stop()