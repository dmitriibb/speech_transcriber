from threading import Lock, Thread
from queue import Queue, Empty
from typing import Optional

from src.output_writer import OutputWriter


class Transcriber:
    def __init__(self, output_writer: OutputWriter):
        self.output_writer = output_writer
        self.chunk_counter = 0
        self._lock = Lock()
        self._processing_queue = Queue()
        self._processing_thread: Optional[Thread] = None
        self._should_stop = False
        self._start_processing_thread()
        
    def _start_processing_thread(self):
        """Start the background thread for processing audio chunks."""
        self._should_stop = False
        self._processing_thread = Thread(target=self._process_chunks, daemon=True)
        self._processing_thread.start()
        
    def _process_chunks(self):
        """Background thread function to process audio chunks."""
        while not self._should_stop:
            self._process_chunk_from_queue()

    def _process_chunk_from_queue(self):
        try:
            chunk_audio = self._processing_queue.get(timeout=1.0)  # 1 second timeout
            with self._lock:
                self.chunk_counter += 1
            chunk_transcribed = self._transcribe(chunk_audio)
            self.output_writer.write(chunk_transcribed)
            self._processing_queue.task_done()
        except Empty:
            pass # No chunks to process, continue waiting
        
    def transcribe(self, chunk_audio):
        """Synchronous transcription - mainly for testing purposes."""
        chunk_transcribed = self._transcribe(chunk_audio)
        self.output_writer.write(chunk_transcribed)

    def transcribe_async(self, chunk_audio):
        """
        Non-blocking transcription of audio chunk.
        Puts the chunk into a queue for background processing.
        """
        self._processing_queue.put(chunk_audio)

    def _transcribe(self, chunk_audio) -> str:
        return self._dummy_transcribe(chunk_audio)

    def _dummy_transcribe(self, chunk_audio) -> str:
        """Dummy transcription as per requirements."""
        return f"chunk: {self.chunk_counter}, size: {chunk_audio.nbytes} bytes"

    def stop(self):
        """Stop the transcriber and its background processing."""
        self._should_stop = True
        while not self._processing_queue.empty():
            self._process_chunk_from_queue()
        self.output_writer.stop()
