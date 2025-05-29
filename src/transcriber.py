from threading import Lock, Thread
from queue import Queue, Empty
from typing import Optional
import speech_recognition as sr
import numpy as np
import io
import wave

from src.configs import TranscriberConfig
from src.logger import logger
from src.output_writer import OutputWriter
from src.constants import *


class Transcriber:
    def __init__(self, output_writer: OutputWriter, config: TranscriberConfig):
        self.output_writer = output_writer
        self.recognizer_name = config.recogniser_name
        self.chunk_counter = 0
        self._lock = Lock()
        self._processing_queue = Queue()
        self._processing_thread: Optional[Thread] = None
        self._should_stop = False
        self._recognizer = sr.Recognizer()
        self._start_processing_thread()
        
    def _start_processing_thread(self):
        self._should_stop = False
        self._processing_thread = Thread(target=self._process_chunks, daemon=True)
        self._processing_thread.start()
        logger.log("Transcriber start")
        
    def _process_chunks(self):
        while not self._should_stop:
            self._process_chunk_from_queue()

    def _process_chunk_from_queue(self):
        try:
            chunk_audio = self._processing_queue.get(timeout=1.0)
            with self._lock:
                chunk_transcribed = self._transcribe(chunk_audio)
                self.chunk_counter += 1
                logger.log(f"Transcriber chunk {self.chunk_counter}")
                self.output_writer.write(chunk_transcribed)
                self._processing_queue.task_done()
        except Empty:
            pass # No chunks to process, continue waiting
        
    def transcribe(self, chunk_audio):
        chunk_transcribed = self._transcribe(chunk_audio)
        if chunk_transcribed:
            self.output_writer.write(chunk_transcribed)

    def transcribe_async(self, chunk_audio):
        self._processing_queue.put(chunk_audio)

    def _transcribe(self, chunk_audio) -> str:
        if self.recognizer_name == recogniserDummy:
            return self._transcribe_dummy(chunk_audio)
        elif self.recognizer_name == recogniserSphinx:
            return self._transcribe_sphinx(chunk_audio)
        elif self.recognizer_name == recogniserGoogleCloud:
            return self._transcribe_google_cloud(chunk_audio)
        else:
            raise Exception(f"recogniser {self.recognizer_name} is not supported")

    def _transcribe_dummy(self, chunk_audio) -> str:
        return f"chunk: {self.chunk_counter}, size: {chunk_audio.nbytes} bytes"

    def _transcribe_sphinx(self, chunk_audio) -> str:
        try:
            wav_bytes = self._numpy_to_wav(chunk_audio)
            audio_data = sr.AudioData(wav_bytes, sample_rate=16000, sample_width=2)

            try:
                text = self._recognizer.recognize_sphinx(audio_data)
                return text
            except sr.UnknownValueError:
                return ""  # No speech detected
            except sr.RequestError as e:
                logger.log(f"Error during transcription: {e}")
                return ""

        except Exception as e:
            logger.log(f"Error processing audio chunk: {e}")
            return ""

    def _transcribe_google_cloud(self, chunk_audio) -> str:
        try:
            wav_bytes = self._numpy_to_wav(chunk_audio)
            audio_data = sr.AudioData(wav_bytes, sample_rate=16000, sample_width=2)

            try:
                text = self._recognizer.recognize_google(audio_data)
                return text
            except sr.UnknownValueError:
                return ""  # No speech detected
            except sr.RequestError as e:
                logger.log(f"Error during transcription: {e}")
                return ""

        except Exception as e:
            logger.log(f"Error processing audio chunk: {e}")
            return ""

    def _numpy_to_wav(self, audio_chunk: np.ndarray) -> bytes:
        """Convert numpy array to WAV format bytes."""
        # Ensure audio is float32 and normalized between -1 and 1
        if audio_chunk.dtype != np.float32:
            audio_chunk = audio_chunk.astype(np.float32)
        
        # Convert to int16 for WAV format
        audio_int16 = (audio_chunk * 32767).astype(np.int16)
        
        # Create WAV file in memory
        bytes_io = io.BytesIO()
        with wave.open(bytes_io, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample (16 bits)
            wav_file.setframerate(16000)  # Sample rate
            wav_file.writeframes(audio_int16.tobytes())
        
        return bytes_io.getvalue()

    def stop(self):
        """Stop the transcriber and its background processing."""
        self._should_stop = True
        while not self._processing_queue.empty():
            self._process_chunk_from_queue()
        self.output_writer.stop()
