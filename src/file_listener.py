import os
from threading import Thread


from logger import logger
from model import ListenerBase


class FileListener(ListenerBase):
    def __init__(self, transcriber):
        self.transcriber = transcriber
        self.is_running = False
        self.input_file = None
        self._processing_thread = None

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
        logger.log("FileListener stopping")

        if self._processing_thread is not None and self._processing_thread.is_alive():
            try:
                self._processing_thread._stop()
                logger.log("FileListener interrupted current file processing")
            except Exception as e:
                logger.error(f"FileListener can't interrupted current file processing: {e}."
                             f" You need to manually close the app or wait until transcription is finished")
        logger.log("FileListener stop")

    def _process_file(self):
        self.transcriber.transcribe_file(self.input_file)
        self.transcriber.stop()