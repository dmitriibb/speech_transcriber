import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sounddevice as sd
import os
from audio_listener import AudioListener
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
        
        # Initialize components
        self.audio_listener = AudioListener()
        
        self._create_widgets()
        
    def _create_widgets(self):
        # Input source selection
        input_frame = ttk.LabelFrame(self.root, text="Audio Input Source", padding="10")
        input_frame.pack(fill="x", padx=10, pady=5)
        
        self.input_dropdown = ttk.Combobox(
            input_frame, 
            textvariable=self.selected_input,
            state="readonly"
        )
        self.input_dropdown['values'] = self._get_input_devices()
        self.input_dropdown.pack(fill="x")
        
        # Output directory selection
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
        
        # Start/Stop button
        self.control_btn = ttk.Button(
            self.root,
            text="Start",
            command=self._toggle_transcription
        )
        self.control_btn.pack(pady=20)
        
    def _get_input_devices(self):
        """Get list of all available input devices."""
        devices = sd.query_devices()
        input_devices = [dev['name'] for dev in devices if dev['max_input_channels'] > 0]
        return input_devices
        
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
        output_writer = OutputWriter()
        output_writer.set_output_directory(self.output_directory.get())
        output_writer.start_new_file()

        transcriber = Transcriber(output_writer)
        
        self.audio_listener.set_input_device(self.selected_input.get())
        self.audio_listener.start(transcriber)
        
        self.transcribing = True
        self.control_btn.configure(text="Stop")

    def _stop_transcribing(self):
        """Stop the transcription process."""
        self.audio_listener.stop()
        
        self.transcribing = False
        self.control_btn.configure(text="Start")


def main():
    root = tk.Tk()
    app = TranscriberApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 