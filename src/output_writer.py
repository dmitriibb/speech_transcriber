import os
from datetime import datetime
from threading import Lock
from typing import Optional, Callable

from src.configs import OutputConfig
from src.logger import logger
from src.model import ChunkTranscribed


class OutputWriter:
    def __init__(self, config: OutputConfig, on_error: Optional[Callable] = None):
        self.output_directory = config.output_directory
        self.on_error = on_error
        self._lock = Lock()
        self._current_file = None

    def get_output_directory(self) -> str:
        return self.output_directory

    def start_new_file(self) -> int:
        """Start a new transcription file"""
        with self._lock:
            if self._current_file is not None:
                self._current_file.close()

            # Create output directory if it doesn't exist
            if not os.path.exists(self.output_directory):
                os.makedirs(self.output_directory)

            # Create new file
            file_number = self._get_next_file_number()
            filename = f"transcription-{file_number}.txt"
            filepath = os.path.join(self.output_directory, filename)
            try:
                self._current_file = open(filepath, "w", encoding="utf-8")
                self._current_file.write(f"Transcription started at {datetime.now()}\n\n")
                logger.log(f"Created new transcription file: {filename}")
            except Exception as e:
                logger.log(f"Error creating transcription file: {e}")
                if self.on_error:
                    self.on_error()
        return file_number

    def _get_next_file_number(self):
        existing_files = [f for f in os.listdir(self.output_directory)
                          if f.startswith("transcription-") and f.endswith(".txt")]
        if not existing_files:
            return 1

        numbers = [int(f.split("-")[1].split(".")[0]) for f in existing_files]
        return max(numbers) + 1

    def write(self, chunk: ChunkTranscribed):
        """Write a transcribed chunk to the current file"""
        if not chunk.text.strip():
            return

        with self._lock:
            if self._current_file is None:
                self.start_new_file()

            try:
                # Format the text with speaker name if available
                if chunk.speaker_name:
                    text = f"{chunk.speaker_name}: {chunk.text}\n"
                else:
                    text = f"{chunk.text}\n"

                self._current_file.write(text)
                self._current_file.flush()
                logger.log(f"OutputWriter {chunk.speaker_name}: chunk {chunk.index}")
            except Exception as e:
                logger.error(f"Error writing to transcription file: {e}")
                if self.on_error:
                    self.on_error()

    def stop(self):
        """Close the current transcription file"""
        with self._lock:
            if self._current_file is not None:
                try:
                    self._current_file.write(f"\nTranscription ended at {datetime.now()}\n")
                    self._current_file.close()
                    self._current_file = None
                except Exception as e:
                    logger.log(f"Error closing transcription file: {e}")
                    if self.on_error:
                        self.on_error()
