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
        logger.log("FileListener start")

    def stop(self):
        logger.log("FileListener finished")

    def _process_file(self):
        # Load audio file using pydub
        self.transcriber.transcribe_file(self.input_file)
        self.stop()
        self.transcriber.stop()