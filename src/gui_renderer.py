import tkinter as tk
from enum import Enum
from tkinter import ttk, filedialog, messagebox

from audio_devices import get_devices_names
from model import InputMode, AudioInputLine
from actions import TranscriberActions
from constants import recogniserDummy, recogniserSphinx, recogniserGoogleCloud
from gui_utils import get_available_models, get_downloaded_models, format_model_name
import whisper
import threading


class MainProps:
    def __init__(self, input_mode: InputMode):
        self.input_mode = tk.StringVar(value=input_mode.value)

class LiveListenProps:
    def __init__(self):
        self.audio_input_lines = []  # List of AudioInputLine objects
        self.include_output_devices = tk.BooleanVar(value=False)
        self.next_speaker_name = 'A'  # For auto-generating speaker names

    def add_input_line(self):
        """Add a new audio input line with default values"""
        new_line = AudioInputLine(
            device_name="",
            speaker_name=self.next_speaker_name,
            record=False,
            transcribe=True
        )
        self.audio_input_lines.append(new_line)
        self._increment_speaker_name()
        return new_line

    def remove_input_line(self, index: int):
        """Remove an audio input line by index"""
        if 0 <= index < len(self.audio_input_lines):
            self.audio_input_lines.pop(index)

    def _increment_speaker_name(self):
        """Get next speaker name (A -> B -> C etc)"""
        self.next_speaker_name = chr(ord(self.next_speaker_name) + 1)
        if self.next_speaker_name > 'Z':
            self.next_speaker_name = 'A'

class FileListenProps:
    def __init__(self):
        self.selected_file =  tk.StringVar()

class OutputProps:
    def __init__(self, output_directory: str, tmp_directory: str):
        self.output_directory = tk.StringVar(value=output_directory)
        self.tmp_directory = tk.StringVar(value=tmp_directory)

class RecognizerProps:
    def __init__(self, default_recognizer: str):
        self.selected_recognizer = tk.StringVar(value=default_recognizer)
        self.chunk_duration = tk.StringVar(value="5")
        self.use_ai = tk.BooleanVar(value=False)
        self.selected_ai_model = tk.StringVar()
        self.ai_model_dropdown = None

class StatusProps:
    def __init__(self, default_status: str):
        self.status = tk.StringVar(value=default_status)
        self.start_button = None
        self.transcribing = False

class LogsProps:
    def __init__(self):
        self.logs_text = None

class GuiRenderer:

    def __init__(self, root: tk.Tk, 
                 main_props: MainProps, 
                 live_listen_props: LiveListenProps, 
                 file_listen_props: FileListenProps,
                 output_props: OutputProps,
                 recognizer_props: RecognizerProps,
                 status_props: StatusProps,
                 logs_props: LogsProps,
                 actions: TranscriberActions):
        self.root = root
        self.main_props = main_props
        self.live_listen_props = live_listen_props
        self.file_listen_props = file_listen_props
        self.output_props = output_props
        self.recognizer_props = recognizer_props
        self.status_props = status_props
        self.logs_props = logs_props
        self.actions = actions

        self.input_frame = None
        self.file_frame = None
        self.live_frame = None

    def render_main(self):
        mode_frame = ttk.LabelFrame(self.root, text="Input Mode", padding="10")
        mode_frame.pack(fill="x", padx=10, pady=5)

        # Create radio buttons for mode selection
        live_radio = ttk.Radiobutton(
            mode_frame,
            text=InputMode.LIVE.value,
            variable=self.main_props.input_mode,
            value=InputMode.LIVE.value,
            command=self._update_input_mode
        )
        live_radio.pack(side="left", padx=5)

        file_radio = ttk.Radiobutton(
            mode_frame,
            text=InputMode.FILE.value,
            variable=self.main_props.input_mode,
            value=InputMode.FILE.value,
            command=self._update_input_mode
        )
        file_radio.pack(side="left", padx=5)

    def render_live_listen(self):
        self._render_input_frame()
        self.live_frame = ttk.Frame(self.input_frame)

        # Add button to add new input line
        add_button = ttk.Button(
            self.live_frame,
            text="Add Input",
            command=self._add_input_line
        )
        add_button.pack(fill="x", pady=(0, 5))

        # Container for input lines
        self.input_lines_frame = ttk.Frame(self.live_frame)
        self.input_lines_frame.pack(fill="x")

        # Add checkbox for output devices
        include_output_checkbox = ttk.Checkbutton(
            self.live_frame,
            text="Include output devices",
            variable=self.live_listen_props.include_output_devices,
            command=self._refresh_input_devices
        )
        include_output_checkbox.pack(fill="x", pady=(5, 0))

        # Add initial input line
        if not self.live_listen_props.audio_input_lines:
            self._add_input_line()

        self._update_input_mode()

    def _add_input_line(self):
        """Add a new audio input line to the UI"""
        new_line = self.live_listen_props.add_input_line()
        self._render_input_line(new_line, len(self.live_listen_props.audio_input_lines) - 1)

    def _render_input_line(self, input_line: AudioInputLine, index: int):
        """Render a single audio input line"""
        line_frame = ttk.Frame(self.input_lines_frame)
        line_frame.pack(fill="x", pady=(0, 5))

        # Remove button
        remove_btn = ttk.Button(
            line_frame,
            text="-",
            width=3,
            command=lambda: self._remove_input_line(index)
        )
        remove_btn.pack(side="left", padx=(0, 5))

        # Audio device dropdown
        device_dropdown = ttk.Combobox(
            line_frame,
            state="readonly",
            width=50
        )
        device_dropdown['values'] = self._get_input_devices()
        device_dropdown.set(input_line.device_name if input_line.device_name else "")
        device_dropdown.pack(side="left", padx=(0, 5))

        # Bind the dropdown selection to update the input line
        def on_device_select(event):
            input_line.device_name = device_dropdown.get()
        device_dropdown.bind('<<ComboboxSelected>>', on_device_select)

        # Speaker name entry
        speaker_label = ttk.Label(line_frame, text="Speaker:")
        speaker_label.pack(side="left", padx=(5, 2))
        
        speaker_var = tk.StringVar(value=input_line.speaker_name)
        speaker_entry = ttk.Entry(
            line_frame,
            textvariable=speaker_var,
            width=5
        )
        speaker_entry.pack(side="left", padx=(0, 5))

        # Bind the entry to update the input line
        def on_speaker_change(*args):
            input_line.speaker_name = speaker_var.get()
        speaker_var.trace_add("write", on_speaker_change)

        # Record checkbox
        record_var = tk.BooleanVar(value=input_line.record)
        record_check = ttk.Checkbutton(
            line_frame,
            text="Record",
            variable=record_var
        )
        record_check.pack(side="left", padx=(5, 5))

        # Bind the checkbox to update the input line
        def on_record_change(*args):
            input_line.record = record_var.get()
        record_var.trace_add("write", on_record_change)

        # Transcribe checkbox
        transcribe_var = tk.BooleanVar(value=input_line.transcribe)
        transcribe_check = ttk.Checkbutton(
            line_frame,
            text="Transcribe",
            variable=transcribe_var
        )
        transcribe_check.pack(side="left")

        # Bind the checkbox to update the input line
        def on_transcribe_change(*args):
            input_line.transcribe = transcribe_var.get()
        transcribe_var.trace_add("write", on_transcribe_change)

    def _remove_input_line(self, index: int):
        """Remove an input line from the UI"""
        self.live_listen_props.remove_input_line(index)
        # Destroy all input lines and re-render them
        for child in self.input_lines_frame.winfo_children():
            child.destroy()
        # Re-render all input lines
        for i, line in enumerate(self.live_listen_props.audio_input_lines):
            self._render_input_line(line, i)

    def _get_input_devices(self):
        return get_devices_names(self.live_listen_props.include_output_devices.get())

    def _refresh_input_devices(self):
        new_values = self._get_input_devices()
        
        # Refresh all input line dropdowns
        for child in self.input_lines_frame.winfo_children():
            # Find the device dropdown in this input line frame
            for widget in child.winfo_children():
                if isinstance(widget, ttk.Combobox):
                    current_selection = widget.get()
                    widget['values'] = new_values
                    
                    # Keep current selection if it's still valid
                    if current_selection in new_values:
                        widget.set(current_selection)
                    else:
                        widget.set('')
                    break

    def render_file_listen(self):
        self._render_input_frame()
        self.file_frame = ttk.Frame(self.input_frame)

        file_entry = ttk.Entry(
            self.file_frame,
            textvariable=self.file_listen_props.selected_file,
            state="readonly"
        )
        file_entry.pack(side="left", fill="x", expand=True)

        choose_file_btn = ttk.Button(
            self.file_frame,
            text="Choose File",
            command=self._choose_input_file
        )
        choose_file_btn.pack(side="right", padx=(5, 0))
        self._update_input_mode()

    def _choose_input_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.m4a *.aac *.ogg"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.file_listen_props.selected_file.set(file_path)

    def _render_input_frame(self):
        if self.input_frame is None:
            self.input_frame = ttk.LabelFrame(self.root, text="Audio Input", padding="10")
            self.input_frame.pack(fill="x", padx=10, pady=5)

    def _update_input_mode(self):
        if self.file_frame is None or self.live_frame is None:
            return

        if self.main_props.input_mode.get() == InputMode.LIVE.value:
            self.file_frame.pack_forget()
            self.live_frame.pack(fill="x")
        else:
            self.live_frame.pack_forget()
            self.file_frame.pack(fill="x")

    def render_output_section(self):
        output_frame = ttk.LabelFrame(self.root, text="Output Directory", padding="10")
        output_frame.pack(fill="x", padx=10, pady=5)

        # Output directory section
        output_container = ttk.Frame(output_frame)
        output_container.pack(fill="x", pady=(0, 5))

        output_entry = ttk.Entry(
            output_container,
            textvariable=self.output_props.output_directory,
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
            textvariable=self.output_props.tmp_directory,
            state="readonly"
        )
        tmp_directory_entry.pack(side="left", fill="x", expand=True)

        tmp_directory_choose_btn = ttk.Button(
            tmp_container,
            text="Choose",
            command=self._choose_tmp_directory
        )
        tmp_directory_choose_btn.pack(side="right", padx=(5, 0))

    def render_recognizer_section(self):
        recogniser_frame = ttk.LabelFrame(self.root, text="Speech recognition", padding="10")
        recogniser_frame.pack(fill="x", padx=10, pady=5)

        # Recognizer dropdown
        recogniser_dropdown = ttk.Combobox(
            recogniser_frame,
            textvariable=self.recognizer_props.selected_recognizer,
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
            textvariable=self.recognizer_props.chunk_duration,
            width=10,
            validate="key",
            validatecommand=vcmd
        )
        duration_entry.pack(side="left")

        # AI Section
        ai_frame = ttk.LabelFrame(recogniser_frame, text="AI", padding="10")
        ai_frame.pack(fill="x", pady=(10, 5), expand=True)

        ai_toggle = ttk.Checkbutton(
            ai_frame,
            text="Use AI",
            variable=self.recognizer_props.use_ai,
            command=self._toggle_ai
        )
        ai_toggle.pack(side="left")

        # AI model dropdown
        self.recognizer_props.ai_model_dropdown = ttk.Combobox(
            ai_frame,
            textvariable=self.recognizer_props.selected_ai_model,
            state="disabled"
        )
        self.recognizer_props.ai_model_dropdown.pack(side="left", fill="x", expand=True, padx=(5,0))
        self.recognizer_props.ai_model_dropdown.bind("<<ComboboxSelected>>", self._on_ai_model_select)

    def render_status_section(self):
        status_frame = ttk.LabelFrame(self.root, text="Status", padding="10")
        status_frame.pack(fill="x", padx=10, pady=5)
        status_text = ttk.Label(
            status_frame,
            textvariable=self.status_props.status
        )
        status_text.pack(fill="x")

        self.status_props.start_button = ttk.Button(
            self.root,
            text="Start",
            command=self._toggle_transcription
        )
        self.status_props.start_button.pack(pady=10)

    def render_logs_section(self):
        logs_frame = ttk.LabelFrame(self.root, text="Logs", padding="10")
        logs_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create a frame to hold both the text widget and scrollbar
        text_frame = ttk.Frame(logs_frame)
        text_frame.pack(fill="both", expand=True)

        # Create the text widget
        self.logs_props.logs_text = tk.Text(
            text_frame,
            height=10,
            wrap=tk.WORD,
            state="disabled"
        )
        self.logs_props.logs_text.pack(side="left", fill="both", expand=True)

        # Create the scrollbar
        scrollbar = ttk.Scrollbar(
            text_frame,
            orient="vertical",
            command=self.logs_props.logs_text.yview
        )
        scrollbar.pack(side="right", fill="y")

        # Configure the text widget to use the scrollbar
        self.logs_props.logs_text.configure(yscrollcommand=scrollbar.set)

    def render_all(self):
        self.render_main()
        self.render_live_listen()
        self.render_file_listen()
        self.render_output_section()
        self.render_recognizer_section()
        self.render_status_section()
        self.render_logs_section()

    def _choose_directory(self):
        directory = filedialog.askdirectory(
            initialdir=self.output_props.output_directory.get(),
            title="Select Output Directory"
        )
        if directory:  # If user didn't cancel
            self.output_props.output_directory.set(directory)

    def _choose_tmp_directory(self):
        directory = filedialog.askdirectory(
            initialdir=self.output_props.tmp_directory.get(),
            title="Select tmp Directory"
        )
        if directory:  # If user didn't cancel
            self.output_props.tmp_directory.set(directory)
            self._update_ai_models_dropdown()

    def _toggle_transcription(self):
        if self.status_props.transcribing:
            self.actions.stop_transcribing()
        else:
            self.actions.start_transcribing()

    def _toggle_ai(self):
        if self.recognizer_props.use_ai.get():
            self.recognizer_props.ai_model_dropdown.config(state="readonly")
            self._update_ai_models_dropdown()
        else:
            self.recognizer_props.ai_model_dropdown.config(state="disabled")
            self.recognizer_props.selected_ai_model.set("")

    def _update_ai_models_dropdown(self):
        downloaded_models = get_downloaded_models(self.output_props.tmp_directory.get())
        all_models = get_available_models()
        formatted_models = [format_model_name(m, downloaded_models) for m in all_models]
        self.recognizer_props.ai_model_dropdown['values'] = formatted_models

        # set default selection
        if formatted_models:
            # try to keep current selection if it's still valid
            current_model_full_name = self.recognizer_props.selected_ai_model.get()
            
            if current_model_full_name in formatted_models:
                # model and its status is still the same
                self.recognizer_props.selected_ai_model.set(current_model_full_name)
            else:
                # check if just status changed
                current_model_name = current_model_full_name.split(" - ")[0]
                new_status = "downloaded" if current_model_name in downloaded_models else "to download"
                new_formatted_name = f"{current_model_name} - {new_status}"
                if new_formatted_name in formatted_models:
                    self.recognizer_props.selected_ai_model.set(new_formatted_name)
                else:
                    # select first one
                    self.recognizer_props.selected_ai_model.set(formatted_models[0])

    def _on_ai_model_select(self, event=None):
        selection = self.recognizer_props.selected_ai_model.get()
        model_name = selection.split(" - ")[0]
        
        if "to download" in selection:
            if messagebox.askyesno("Download Model", f"Model '{model_name}' is not downloaded. Do you want to download it?"):
                self._download_model(model_name)

    def _download_model(self, model_name):
        self.status_props.status.set(f"Downloading {model_name} model...")
        self.root.update_idletasks()
        self.status_props.start_button.config(state="disabled")
        self.recognizer_props.ai_model_dropdown.config(state="disabled")

        def do_download():
            try:
                whisper.load_model(model_name, download_root=self.output_props.tmp_directory.get())
                self.status_props.status.set(f"Model {model_name} downloaded.")
                # self._update_ai_models_dropdown() must be called from main thread
                self.root.after(0, self._update_ai_models_dropdown)

            except Exception as e:
                self.status_props.status.set(f"Error downloading {model_name}: {e}")
                messagebox.showerror("Error", f"Failed to download model: {e}")
            finally:
                def reenable_widgets():
                    self.status_props.start_button.config(state="normal")
                    if self.recognizer_props.use_ai.get():
                        self.recognizer_props.ai_model_dropdown.config(state="readonly")
                
                self.root.after(0, reenable_widgets)

        threading.Thread(target=do_download, daemon=True).start()
