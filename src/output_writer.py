import os
from threading import Lock

from src.configs import OutputConfig
from src.logger import logger


class OutputWriter:
    def __init__(self, config: OutputConfig, on_stop_callback=None):
        self.output_dir = config.output_dir
        self.current_file = None
        self._lock = Lock()
        self._on_stop_callback = on_stop_callback
        self.chunk_counter = 0
        
    def _get_next_file_number(self):
        existing_files = [f for f in os.listdir(self.output_dir) 
                         if f.startswith("transcription-") and f.endswith(".txt")]
        if not existing_files:
            return 1
            
        numbers = [int(f.split("-")[1].split(".")[0]) for f in existing_files]
        return max(numbers) + 1
        
    def start_new_file(self):
        if self.output_dir is None:
            raise ValueError("Output directory not set")
            
        file_number = self._get_next_file_number()
        filename = f"transcription-{file_number}.txt"
        self.current_file = os.path.join(self.output_dir, filename)
        
        # Create an empty file
        with open(self.current_file, 'w') as f:
            pass
            
    def write(self, text):
        if self.current_file is None:
            raise ValueError("No active transcription file")
            
        with self._lock:
            if text:
                with open(self.current_file, 'a', encoding='utf-8') as f:
                    f.write(text + "\n")
            self.chunk_counter += 1
            logger.log(f"OutputWriter chunk {self.chunk_counter}")

    def stop(self):
        with self._lock:
            # self.current_file = None
            if self._on_stop_callback:
                self._on_stop_callback()
