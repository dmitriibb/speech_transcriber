from threading import Lock, Thread
from queue import Queue, Empty
from typing import Optional
import speech_recognition as sr
import numpy as np
import io
import os
import wave
import whisper

from src.configs import TranscriberConfig
from src.logger import logger
from src.model import ChunkAudio, ChunkTranscribed
from src.output_writer import OutputWriter
from src.constants import *


class Transcriber:
    def __init__(self, output_writer: OutputWriter, config: TranscriberConfig):
        self.output_writer = output_writer
        self.recognizer_name = config.recogniser_name
        self.tmp_directory = config.tmp_directory
        self.use_ai = config.use_ai
        self.model_name = config.model_name
        self._lock = Lock()
        self._processing_queue = Queue()
        self._processing_thread: Optional[Thread] = None
        self._should_stop = False
        self._recognizer = sr.Recognizer()
        self._whisper_model = None
        self._start_processing_thread()
        self._ready = False

    def init(self):
        if self.use_ai:
            self._load_ai_model()
        self._ready = True
        
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
                transcribed = self._transcribe(chunk_audio)
                logger.log(f"Transcriber chunk {chunk_audio.index}")
                self.output_writer.write(ChunkTranscribed(chunk_audio.index, transcribed))
                self._processing_queue.task_done()
        except Empty:
            pass # No chunks to process, continue waiting
        
    def transcribe_chunk(self, chunk_audio: ChunkAudio):
        if not self._ready:
            raise Exception("Transcriber is not ready")
        transcribed = self._transcribe(chunk_audio)
        if transcribed:
            self.output_writer.write(ChunkTranscribed(chunk_audio.index, transcribed))

    def transcribe_chunk_async(self, chunk_audio: ChunkAudio):
        if not self._ready:
            raise Exception("Transcriber is not ready")
        self._processing_queue.put(chunk_audio)

    def transcribe_file(self, file_path: str):
        transcribed = self._transcribe_file_with_whisper(file_path)
        self.output_writer.write(ChunkTranscribed(1, transcribed))

    def _transcribe(self, chunk_audio: ChunkAudio) -> str:
        if self.use_ai:
            return self._transcribe_whisper(chunk_audio)
        if self.recognizer_name == recogniserDummy:
            return self._transcribe_dummy(chunk_audio)
        elif self.recognizer_name == recogniserSphinx:
            return self._transcribe_sphinx(chunk_audio)
        elif self.recognizer_name == recogniserGoogleCloud:
            return self._transcribe_google_cloud(chunk_audio)
        else:
            raise Exception(f"recogniser {self.recognizer_name} is not supported")

    def _transcribe_dummy(self, chunk_audio: ChunkAudio) -> str:
        return f"chunk: {chunk_audio.index}, size: {chunk_audio.data.nbytes} bytes"

    def _transcribe_sphinx(self, chunk_audio: ChunkAudio) -> str:
        try:
            wav_bytes = self._numpy_to_wav(chunk_audio.data)
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

    def _transcribe_google_cloud(self, chunk_audio: ChunkAudio) -> str:
        try:
            wav_bytes = self._numpy_to_wav(chunk_audio.data)
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

    def _load_ai_model(self):
        if self._whisper_model is None:
            if self.model_name is None:
                raise Exception("AI model name is not configured")
            logger.log(f"Loading Whisper model: {self.model_name}...")
            self._whisper_model = whisper.load_model(
                name=self.model_name,
                download_root=self.tmp_directory
            )
        logger.log("Whisper model loaded")

    def _transcribe_whisper(self, chunk_audio: ChunkAudio) -> str:
        try:
            # Convert numpy array to temporary WAV file
            wav_bytes = self._numpy_to_wav(chunk_audio.data)
            
            # Save to a temporary file since Whisper works with files
            temp_file = "temp_chunk.wav"
            with open(temp_file, "wb") as f:
                f.write(wav_bytes)

            result = self._transcribe_file_with_whisper(temp_file)

            os.remove(temp_file)
            
            return result

        except Exception as e:
            logger.log(f"Error in Whisper transcription: {e}")
            return ""

    def _transcribe_file_with_whisper(self, file_path: str) -> str:
        if self._whisper_model is None:
            raise Exception("Ai model is not loaded")

        result = self._whisper_model.transcribe(file_path)
        return result["text"].strip()

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
