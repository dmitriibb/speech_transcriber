import sounddevice as sd
import numpy as np
from queue import Queue, Empty
from threading import Thread, Event
import wave
import os

from model import AudioDeviceWrapper, ListenerBase, AudioInputLine
from audio_devices import get_device_by_name, SystemSoundRecorder
from configs import AudioListenerConfig
from constants import deviceTypeInput
from logger import Logger, logger
from model import ChunkAudio
from transcriber import Transcriber


class AudioListener(ListenerBase):
    def __init__(self, transcriber: Transcriber, config: AudioListenerConfig):
        self.transcriber = transcriber
        self.chunk_duration = config.chunk_duration
        self.input_line = config.input_line
        self.device_wrapper = get_device_by_name(self.input_line.device_name)
        self.stream = None
        self.stop_event = Event()
        self.audio_queue = Queue()
        self.sample_rate = 16000  # Standard sample rate for speech
        self.listen_thread = None
        self.chunk_counter = 0
        self.recording_file = None
        self.recording_wave = None
        self._transcription_index = config.transcription_index
        self._speaker_name = config.input_line.speaker_name
            
    def start(self):
        if self.device_wrapper is None:
            raise ValueError("Input device not set")

        if self.transcriber is None:
            raise ValueError("Transcriber not set")
            
        self.stop_event.clear()

        # Setup recording if enabled
        if self.input_line.record:
            self._setup_recording()
                        
        self.listen_thread = Thread(target=self._process_audio)
        self.listen_thread.start()
        logger.log(f"Start listening {self.device_wrapper.get_name()}")

    def _setup_recording(self):
        """Setup WAV file for recording"""
        # Create a filename with the speaker name
        filename = f"rec-{self._transcription_index}-{self._speaker_name}.wav"
        self.recording_file = os.path.join(self.transcriber.get_output_directory(), filename)
        
        # Create and setup the WAV file
        self.recording_wave = wave.open(self.recording_file, 'wb')
        self.recording_wave.setnchannels(1)  # Mono
        self.recording_wave.setsampwidth(2)  # 2 bytes per sample (16 bits)
        self.recording_wave.setframerate(self.sample_rate)

    def _audio_callback(self, data, frames, time, status):
        """Callback function for the audio stream."""
        if status:
            logger.log(f'Audio callback status: {status}')
        if not self.stop_event.is_set():
            # Add to transcription queue if transcription is enabled
            if self.input_line.transcribe:
                self.audio_queue.put(data.copy())

            # Save to recording file if enabled
            if self.input_line.record and self.recording_wave:
                audio_int16 = (data * 32767).astype(np.int16)
                self.recording_wave.writeframes(audio_int16.tobytes())

    def _process_audio(self):
        if self.device_wrapper.type == deviceTypeInput:
            self._process_audio_input()
        else:
            self._process_audio_output()

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
                    if self.input_line.transcribe:
                        self.transcriber.transcribe_chunk_async(chunk)
                    self.audio_queue.task_done()
                    logger.log(f"AudioListener {self._speaker_name} chunk {self.chunk_counter}")
                    self.chunk_counter += 1
                except Empty:
                    continue  # No chunks to process, continue waiting

    def _process_audio_output(self):
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
                    if self.input_line.transcribe:
                        self.transcriber.transcribe_chunk_async(chunk)
                    self.audio_queue.task_done()
                    logger.log(f"AudioListener {self._speaker_name} chunk {self.chunk_counter}")
                    self.chunk_counter += 1
                except Empty:
                    continue  # No chunks to process, continue waiting

    def stop(self):
        logger.log(f"AudioListener: {self._speaker_name} stop")
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

        # Close recording file if it was open
        if self.recording_wave:
            self.recording_wave.close()
            self.recording_wave = None

        if self.listen_thread is not None:
            self.listen_thread.join()
            self.listen_thread = None

        # send remaining audio chunks

        while not self.audio_queue.empty():
            logger.log(f"AudioListener: {self._speaker_name} process remaining chunks {self.audio_queue.qsize()}")
            audio_chunk = self.audio_queue.get()
            if self.input_line.transcribe:
                self.transcriber.transcribe_chunk_async(audio_chunk)
            self.audio_queue.task_done()
        self.transcriber.stop()