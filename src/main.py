import tkinter as tk
from enum import Enum
from tkinter import ttk, filedialog, messagebox
import sounddevice as sd
import os

from urllib3.filepost import writer

from audio_listener import AudioListener
from src.audio_devices import get_devices_names
from src.constants import *
from transcriber import Transcriber
from output_writer import OutputWriter



class TranscriberApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speech Transcriber")
        self.root.geometry("600x400")
        
        # State variables
        self.transcribing = False

        self.selected_input = tk.StringVar()
        self.output_directory = tk.StringVar(value=os.path.dirname(os.path.abspath(__file__)))
        self.selected_recognizer = tk.StringVar()
        self.status = tk.StringVar()

        self.audio_listener : AudioListener = None
        
        self._create_widgets()

        # init state
        self.status.set(statusReady)
        self.selected_recognizer.set(recogniserGoogleCloud)
        
    def _create_widgets(self):
        self._audio_source_widget()
        self._output_file_widget()
        self._recogniser_widget()
        self._status_widget()
        self._start_button_widget()


    def _audio_source_widget(self):
        input_frame = ttk.LabelFrame(self.root, text="Audio Input Source", padding="10")
        input_frame.pack(fill="x", padx=10, pady=5)

        input_dropdown = ttk.Combobox(
            input_frame,
            textvariable=self.selected_input,
            state="readonly"
        )
        input_dropdown['values'] = self._get_input_devices()
        input_dropdown.pack(fill="x")

    def _output_file_widget(self):
        output_frame = ttk.LabelFrame(self.root, text="Output Directory", padding="10")
        output_frame.pack(fill="x", padx=10, pady=5)

        output_entry = ttk.Entry(
            output_frame,
            textvariable=self.output_directory,
            state="readonly"
        )
        output_entry.pack(side="left", fill="x", expand=True)

        choose_btn = ttk.Button(
            output_frame,
            text="Choose",
            command=self._choose_directory
        )
        choose_btn.pack(side="right", padx=(5, 0))

    def _recogniser_widget(self):
        recogniser_frame = ttk.LabelFrame(self.root, text="Speech recognition", padding="10")
        recogniser_frame.pack(fill="x", padx=10, pady=5)

        recogniser_dropdown = ttk.Combobox(
            recogniser_frame,
            textvariable=self.selected_recognizer,
            state="readonly"
        )
        recogniser_dropdown['values'] = [recogniserDummy, recogniserSphinx, recogniserGoogleCloud]
        recogniser_dropdown.pack(fill="x")

    def _status_widget(self):
        status_frame = ttk.LabelFrame(self.root, text="Status", padding="10")
        status_frame.pack(fill="x", padx=10, pady=5)
        status_text = ttk.Label(
            status_frame,
            textvariable=self.status
        )
        status_text.pack()

    def _start_button_widget(self):
        self.control_btn = ttk.Button(
            self.root,
            text="Start",
            command=self._toggle_transcription
        )
        self.control_btn.pack(pady=20)
        
    def _get_input_devices(self):
        return get_devices_names()
        
    def _choose_directory(self):
        """Open directory chooser dialog."""
        directory = filedialog.askdirectory(
            initialdir=self.output_directory.get(),
            title="Select Output Directory"
        )
        if directory:  # If user didn't cancel
            self.output_directory.set(directory)
            
    def _toggle_transcription(self):
        """Toggle between Start and Stop states."""
        if self.transcribing:
            self._stop_transcribing()
        else:
            self._start_transcribing()

    def _start_transcribing(self):
        """Start the transcription process."""
        # Validate input source and output directory
        if not self.selected_input.get():
            tk.messagebox.showerror("Error", "Please select an input source")
            return
            
        if not os.path.exists(self.output_directory.get()):
            tk.messagebox.showerror("Error", "Please select a valid output directory")
            return

        # Configure components
        def writer_on_stop_callback():
            self.status.set(statusReady)
        output_writer = OutputWriter(writer_on_stop_callback)
        output_writer.set_output_directory(self.output_directory.get())
        output_writer.start_new_file()

        transcriber = Transcriber(output_writer, self.selected_recognizer.get())

        self.audio_listener = AudioListener(transcriber)
        self.audio_listener.set_input_device_name(self.selected_input.get())
        self.audio_listener.start()
        
        self.transcribing = True
        self.status.set(statusTranscribing)
        self.control_btn.configure(text="Stop")

    def _stop_transcribing(self):
        """Stop the transcription process."""
        self.transcribing = False
        self.status.set(statusFinishing)
        self.audio_listener.stop()

        self.control_btn.configure(text="Start")


def main():
    hostapis = sd.query_hostapis()
    for i, h in enumerate(hostapis):
        print(f"{i}: {h['name']}")

    root = tk.Tk()
    app = TranscriberApp(root)
    root.mainloop()


    #
    # for i, dev in enumerate(sd.query_devices()):
    #     print(f"{i}: {dev['name']} ({dev['hostapi']})")

if __name__ == "__main__":
    main() 