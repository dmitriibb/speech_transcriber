import os
from threading import Lock

class OutputWriter:
    def __init__(self):
        """Initialize the OutputWriter."""
        self.output_dir = None
        self.current_file = None
        self._lock = Lock()
        
    def set_output_directory(self, directory):
        """
        Set the output directory for transcription files.
        
        Args:
            directory (str): Path to the output directory
        """
        self.output_dir = directory
        
    def _get_next_file_number(self):
        """Get the next available file number for transcription file."""
        existing_files = [f for f in os.listdir(self.output_dir) 
                         if f.startswith("transcription-") and f.endswith(".txt")]
        if not existing_files:
            return 1
            
        numbers = [int(f.split("-")[1].split(".")[0]) for f in existing_files]
        return max(numbers) + 1
        
    def start_new_file(self):
        """Create a new transcription file when starting transcription."""
        if self.output_dir is None:
            raise ValueError("Output directory not set")
            
        file_number = self._get_next_file_number()
        filename = f"transcription-{file_number}.txt"
        self.current_file = os.path.join(self.output_dir, filename)
        
        # Create an empty file
        with open(self.current_file, 'w') as f:
            pass
            
    def write(self, text):
        """
        Write transcribed text to the current output file.
        
        Args:
            text (str): Transcribed text to write
        """
        if self.current_file is None:
            raise ValueError("No active transcription file")
            
        with self._lock:
            with open(self.current_file, 'a', encoding='utf-8') as f:
                f.write(text + "\n")

    def stop(self):
        """Stop writing and close the current file."""
        with self._lock:
            self.current_file = None
