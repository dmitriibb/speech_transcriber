from threading import Lock, Thread
from queue import Queue, Empty
from typing import Optional
import speech_recognition as sr
import numpy as np
import io
import os
import wave
import whisper

from configs import TranscriberConfig
from logger import logger
from model import ChunkAudio, ChunkTranscribed
from output_writer import OutputWriter
from constants import *
from ai_model import AiModel


class Transcriber:
    def __init__(self, output_writer: OutputWriter, config: TranscriberConfig, ai_model: AiModel):
        self.output_writer = output_writer
        self._ai_model = ai_model
        self.recognizer_name = config.recogniser_name
        self.tmp_directory = config.tmp_directory
        self.use_ai = config.use_ai
        self.model_name = config.model_name
        self._lock = Lock()
        self._processing_queue = Queue()
        self._processing_thread: Optional[Thread] = None
        self._should_stop = False
        self._recognizer = sr.Recognizer()
        self._start_processing_thread()
        self._ready = False
        self._transcription_index = config.transcription_index
        self.speaker_name = config.speaker_name

    def init(self):
        self._ready = True

    def get_output_directory(self) -> str:
        return self.output_writer.get_output_directory()
        
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
                logger.log(f"Transcriber {self.speaker_name} chunk {chunk_audio.index}")
                self.output_writer.write(ChunkTranscribed(chunk_audio.index, transcribed, self.speaker_name))
                self._processing_queue.task_done()
        except Empty:
            pass # No chunks to process, continue waiting
        
    def transcribe_chunk(self, chunk_audio: ChunkAudio, speaker_name: Optional[str] = None):
        if not self._ready:
            raise Exception(f"Transcriber {self.speaker_name} is not ready")
        transcribed = self._transcribe(chunk_audio)
        if transcribed:
            self.output_writer.write(ChunkTranscribed(chunk_audio.index, transcribed, speaker_name))

    def transcribe_chunk_async(self, chunk_audio: ChunkAudio):
        if not self._ready:
            raise Exception("Transcriber is not ready")
        self._processing_queue.put(chunk_audio)

    def transcribe_file(self, file_path: str):
        transcribed = self._transcribe_file_with_ai(file_path)
        logger.log(f"Transcriber {self.speaker_name}: file transcribe finished, now formatting the output")
        formatted_text = self._format_sentences(transcribed)
        logger.log(f"Transcriber {self.speaker_name}: formatting finished")
        self.output_writer.write(ChunkTranscribed(1, formatted_text))

    def _format_sentences(self, text: str) -> str:
        """Format text so each sentence starts on a new line."""
        # Replace common sentence endings with the ending + newline
        for ending in ['. ', '! ', '? ']:
            text = text.replace(ending, ending + '\n')
        # Remove any extra newlines that might have been created
        text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
        return text

    def _transcribe(self, chunk_audio: ChunkAudio) -> str:
        if self.use_ai:
            return self._transcribe_ai(chunk_audio)
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

    def _transcribe_ai(self, chunk_audio: ChunkAudio) -> str:
        try:
            wav_bytes = self._numpy_to_wav(chunk_audio.data)
            
            # Save to a temporary file since Whisper works with files
            temp_file = f"temp_chunk_{self.speaker_name}.wav"
            with open(temp_file, "wb") as f:
                f.write(wav_bytes)

            result = self._transcribe_file_with_ai(temp_file)
            os.remove(temp_file)
            return result

        except Exception as e:
            logger.log(f"Error in Whisper transcription: {e}")
            return ""

    def _transcribe_file_with_ai(self, file_path: str) -> str:
        if self._ai_model is None:
            raise Exception("Ai model is not loaded")

        result = self._ai_model.transcribe(file_path)
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
        logger.log(f"Transcriber {self.speaker_name}:  stop")
        self._should_stop = True
        while not self._processing_queue.empty():
            self._process_chunk_from_queue()
            logger.log(f"Transcriber {self.speaker_name}: process remaining chunks {self._processing_queue.qsize()}")
        self.output_writer.stop()
