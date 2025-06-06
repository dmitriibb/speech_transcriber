import tkinter as tk
from enum import Enum
from tkinter import ttk, filedialog, messagebox
import sounddevice as sd
import os

from urllib3.filepost import writer

from audio_listener import AudioListener
from file_listener import FileListener
from src.audio_devices import get_devices_names
from src.configs import OutputConfig, TranscriberConfig, AudioListenerConfig
from src.constants import *
from src.logger import Logger, logger
from transcriber import Transcriber
from output_writer import OutputWriter

class InputMode(Enum):
    LIVE = "Live"
    FILE = "File"

class TranscriberApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Speech Transcriber")
        self.root.geometry("600x600")
        
        # State variables
        self.transcribing = False
        self.logger = Logger()

        self.input_mode = tk.StringVar(value=InputMode.LIVE.value)
        self.selected_input = tk.StringVar()
        self.input_file = tk.StringVar()

        base_directory = os.path.dirname(os.path.abspath(__file__))
        head, tail = os.path.split(base_directory)
        if tail == "src":
            output_directory = os.path.join(head, "output")
            tmp_directory = os.path.join(head, "tmp")
        else:
            output_directory = base_directory
            tmp_directory = os.path.join(base_directory, "tmp")

        self.output_directory = tk.StringVar(value=output_directory)
        self.tmp_directory = tk.StringVar(value=tmp_directory)
        self.selected_recognizer = tk.StringVar()
        self.status = tk.StringVar()
        self.include_output_devices = tk.BooleanVar(value=False)
        self.chunk_duration = tk.StringVar(value="5")
        self.use_ai = tk.BooleanVar(value=False)

        self.audio_listener : AudioListener = None
        self.file_listener : FileListener = None
        
        self._create_widgets()

        # init state
        self.status.set(statusReady)
        self.selected_recognizer.set(recogniserGoogleCloud)
        
    def _create_widgets(self):
        self._input_mode_widget()
        self._audio_source_widget()
        self._output_file_widget()
        self._recogniser_widget()
        self._status_widget()
        self._start_button_widget()
        self._logs_widget()

    def _input_mode_widget(self):
        mode_frame = ttk.LabelFrame(self.root, text="Input Mode", padding="10")
        mode_frame.pack(fill="x", padx=10, pady=5)

        # Create radio buttons for mode selection
        live_radio = ttk.Radiobutton(
            mode_frame,
            text=InputMode.LIVE.value,
            variable=self.input_mode,
            value=InputMode.LIVE.value,
            command=self._update_input_mode
        )
        live_radio.pack(side="left", padx=5)

        file_radio = ttk.Radiobutton(
            mode_frame,
            text=InputMode.FILE.value,
            variable=self.input_mode,
            value=InputMode.FILE.value,
            command=self._update_input_mode
        )
        file_radio.pack(side="left", padx=5)

    def _audio_source_widget(self):
        self.input_frame = ttk.LabelFrame(self.root, text="Audio Input", padding="10")
        self.input_frame.pack(fill="x", padx=10, pady=5)

        # Live input widgets
        self.live_frame = ttk.Frame(self.input_frame)
        
        # Create a container frame for dropdown and checkbox
        container = ttk.Frame(self.live_frame)
        container.pack(fill="x")

        # Add the dropdown on the left side
        self.audio_device_dropdown = ttk.Combobox(
            container,
            textvariable=self.selected_input,
            state="readonly"
        )
        self.audio_device_dropdown['values'] = self._get_input_devices()
        self.audio_device_dropdown.pack(side="left", fill="x", expand=True)

        # Add the checkbox on the right side
        include_output_checkbox = ttk.Checkbutton(
            container,
            text="Include output devices",
            variable=self.include_output_devices,
            command=self._refresh_input_devices
        )
        include_output_checkbox.pack(side="right", padx=(5, 0))

        # File input widgets
        self.file_frame = ttk.Frame(self.input_frame)
        
        file_entry = ttk.Entry(
            self.file_frame,
            textvariable=self.input_file,
            state="readonly"
        )
        file_entry.pack(side="left", fill="x", expand=True)

        choose_file_btn = ttk.Button(
            self.file_frame,
            text="Choose File",
            command=self._choose_input_file
        )
        choose_file_btn.pack(side="right", padx=(5, 0))

        # Show initial frame based on mode
        self._update_input_mode()

    def _update_input_mode(self):
        if self.input_mode.get() == InputMode.LIVE.value:
            self.file_frame.pack_forget()
            self.live_frame.pack(fill="x")
        else:
            self.live_frame.pack_forget()
            self.file_frame.pack(fill="x")

    def _choose_input_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.m4a *.aac *.ogg"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.input_file.set(file_path)

    def _output_file_widget(self):
        output_frame = ttk.LabelFrame(self.root, text="Output Directory", padding="10")
        output_frame.pack(fill="x", padx=10, pady=5)

        # Output directory section
        output_container = ttk.Frame(output_frame)
        output_container.pack(fill="x", pady=(0, 5))

        output_entry = ttk.Entry(
            output_container,
            textvariable=self.output_directory,
            state="readonly"
        )
        output_entry.pack(side="left", fill="x", expand=True)

        choose_btn = ttk.Button(
            output_container,
            text="Choose",
            command=self._choose_directory
        )
        choose_btn.pack(side="right", padx=(5, 0))

        # Tmp directory section
        tmp_container = ttk.Frame(output_frame)
        tmp_container.pack(fill="x")

        tmp_directory_entry = ttk.Entry(
            tmp_container,
            textvariable=self.tmp_directory,
            state="readonly"
        )
        tmp_directory_entry.pack(side="left", fill="x", expand=True)

        tmp_directory_choose_btn = ttk.Button(
            tmp_container,
            text="Choose",
            command=self._choose_tmp_directory
        )
        tmp_directory_choose_btn.pack(side="right", padx=(5, 0))

    def _recogniser_widget(self):
        recogniser_frame = ttk.LabelFrame(self.root, text="Speech recognition", padding="10")
        recogniser_frame.pack(fill="x", padx=10, pady=5)

        # Recognizer dropdown
        recogniser_dropdown = ttk.Combobox(
            recogniser_frame,
            textvariable=self.selected_recognizer,
            state="readonly"
        )
        recogniser_dropdown['values'] = [recogniserDummy, recogniserSphinx, recogniserGoogleCloud]
        recogniser_dropdown.pack(fill="x", pady=(0, 5))

        # Chunk duration input
        duration_frame = ttk.Frame(recogniser_frame)
        duration_frame.pack(fill="x", pady=(5, 0))

        duration_label = ttk.Label(duration_frame, text="Chunk duration (sec):")
        duration_label.pack(side="left", padx=(0, 5))

        def validate_numeric(P):
            if P == "": return True
            try:
                float(P)
                return True
            except ValueError:
                return False

        vcmd = (self.root.register(validate_numeric), '%P')
        duration_entry = ttk.Entry(
            duration_frame,
            textvariable=self.chunk_duration,
            width=10,
            validate="key",
            validatecommand=vcmd
        )
        duration_entry.pack(side="left")

        # AI Section
        ai_frame = ttk.Frame(recogniser_frame)
        ai_frame.pack(fill="x", pady=(0, 5))

        ai_toggle = ttk.Checkbutton(
            ai_frame,
            text="Enable AI",
            variable=self.use_ai
        )
        ai_toggle.pack(side="left")

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

    def _logs_widget(self):
        logs_frame = ttk.LabelFrame(self.root, text="Logs", padding="10")
        logs_frame.pack(fill="x", padx=10, pady=5)

        # Create a frame to hold both the text widget and scrollbar
        text_frame = ttk.Frame(logs_frame)
        text_frame.pack(fill="both", expand=True)

        # Create the text widget
        self.logs_text = tk.Text(
            text_frame,
            height=7,
            wrap=tk.WORD,
            state="disabled"
        )
        self.logs_text.pack(side="left", fill="both", expand=True)

        # Create the scrollbar
        scrollbar = ttk.Scrollbar(
            text_frame,
            orient="vertical",
            command=self.logs_text.yview
        )
        scrollbar.pack(side="right", fill="y")

        # Configure the text widget to use the scrollbar
        self.logs_text.configure(yscrollcommand=scrollbar.set)

        def log(message):
            self.logs_text.configure(state="normal")
            self.logs_text.insert("end", f"{message}\n")
            self.logs_text.see("end")  # Auto-scroll to the bottom
            self.logs_text.configure(state="disabled")
        logger.set_log_func(log)
        # self.log_all_devices()

        def show_error(message):
            tk.messagebox.showerror("Error", message)
        logger.set_show_error_func(show_error)

    def _get_input_devices(self):
        return get_devices_names(self.include_output_devices.get())

    def _refresh_input_devices(self):
        current_selection = self.selected_input.get()
        new_values = self._get_input_devices()
        self.audio_device_dropdown['values'] = new_values

        if current_selection in new_values:
            self.selected_input.set(current_selection)
        else:
            self.selected_input.set('')

    def _choose_directory(self):
        directory = filedialog.askdirectory(
            initialdir=self.output_directory.get(),
            title="Select Output Directory"
        )
        if directory:  # If user didn't cancel
            self.output_directory.set(directory)

    def _choose_tmp_directory(self):
        directory = filedialog.askdirectory(
            initialdir=self.tmp_directory.get(),
            title="Select tmp Directory"
        )
        if directory:  # If user didn't cancel
            self.tmp_directory.set(directory)
            
    def _toggle_transcription(self):
        if self.transcribing:
            self._stop_transcribing()
        else:
            self._start_transcribing()

    def _start_transcribing(self):
        try:
            output_config = OutputConfig(self.output_directory.get())

            def writer_on_stop_callback():
                self.status.set(statusReady)
            output_writer = OutputWriter(output_config, writer_on_stop_callback)
            output_writer.start_new_file()

            transcriber_config = TranscriberConfig(self.selected_recognizer.get(), self.use_ai.get())
            transcriber = Transcriber(output_writer, transcriber_config)

            live_transcribe = self.input_mode.get() == InputMode.LIVE.value
            if live_transcribe:
                transcriber.init()
                chunk_duration = int(self.chunk_duration.get())
                audio_listener_config = AudioListenerConfig(self.selected_input.get(), chunk_duration)
                self.audio_listener = AudioListener(transcriber, audio_listener_config)
            else:
                transcriber.use_ai = True
                transcriber.init()
                if not self.input_file.get():
                    raise ValueError("Please select an input file")
                self.audio_listener = FileListener(transcriber)

            self.audio_listener.start()
            self.status.set(statusTranscribing)
            self.transcribing = True
            self.control_btn.configure(text="Stop")
        except Exception as e:
            logger.show_error(f"Failed to start transcription: {str(e)}")
            return

    def _stop_transcribing(self):
        """Stop the transcription process."""
        self.transcribing = False
        self.status.set(statusFinishing)
        self.audio_listener.stop()
        self.audio_listener = None

        self.control_btn.configure(text="Start")

    def log_all_devices(self):
        hostapis = sd.query_hostapis()
        for i, h in enumerate(hostapis):
            logger.log(f"{i}: {h['name']}")
        for i, dev in enumerate(sd.query_devices()):
            logger.log(f"{i}: {dev['name']} ({dev['hostapi']})")

def main():
    root = tk.Tk()
    app = TranscriberApp(root)
    root.mainloop()


if __name__ == "__main__":
    main() 