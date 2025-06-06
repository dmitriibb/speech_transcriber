import os
import wave
from threading import Thread

import numpy as np
from pydub import AudioSegment
import soundfile as sf
import io

from src.logger import logger


class FileListener:
    def __init__(self, transcriber):
        self.transcriber = transcriber
        self.is_running = False
        self.input_file = None

    def set_input_file(self, file_path):
        """Set the input file path to process"""
        self.input_file = file_path

    def start(self):
        """Start processing the input file"""
        if not self.input_file or not os.path.exists(self.input_file):
            raise ValueError("No input file specified or file does not exist")

        self._processing_thread = Thread(target=self._process_file, daemon=True)
        self._processing_thread.start()
        logger.log("Transcriber start")

    def stop(self):
        pass

    def _process_file(self):
        # Load audio file using pydub
        audio = AudioSegment.from_file(self.input_file)
        
        # Convert to wav format in memory
        wav_io = io.BytesIO()
        audio.export(wav_io, format='wav')
        wav_io.seek(0)
        
        # Read the wav data
        with sf.SoundFile(wav_io) as wav_file:
            audio_data = wav_file.read()
            sample_rate = wav_file.samplerate

        # Send the entire audio to transcriber
        if self.is_running:
            self.transcriber.transcribe_chunk(audio_data, sample_rate=sample_rate)