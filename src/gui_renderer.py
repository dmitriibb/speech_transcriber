import tkinter as tk
from enum import Enum
from tkinter import ttk, filedialog, messagebox

from src.audio_devices import get_devices_names
from src.model import InputMode


class MainProps:
    def __init__(self, input_mode: InputMode):
        self.input_mode = tk.StringVar(value=input_mode.value)

class LiveListenProps:
    def __init__(self):
        self.selected_live_device =  tk.StringVar()
        self.include_output_devices = tk.BooleanVar(value=False)

class FileListenProps:
    def __init__(self):
        self.selected_file =  tk.StringVar()

class GuiRenderer:

    def __init__(self, root: tk.Tk, main_props: MainProps, live_listen_props: LiveListenProps, file_listen_props: FileListenProps):
        self.root = root
        self.main_props = main_props
        self.live_listen_props = live_listen_props
        self.file_listen_props = file_listen_props

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

        # Create a container frame for dropdown and checkbox
        container = ttk.Frame(self.live_frame)
        container.pack(fill="x")

        # Add the dropdown on the left side
        self.audio_device_dropdown = ttk.Combobox(
            container,
            textvariable=self.live_listen_props.selected_live_device,
            state="readonly"
        )
        self.audio_device_dropdown['values'] = self._get_input_devices()
        self.audio_device_dropdown.pack(side="left", fill="x", expand=True)

        # Add the checkbox on the right side
        include_output_checkbox = ttk.Checkbutton(
            container,
            text="Include output devices",
            variable=self.live_listen_props.include_output_devices,
            command=self._refresh_input_devices
        )
        include_output_checkbox.pack(side="right", padx=(5, 0))
        self._update_input_mode()

    def _get_input_devices(self):
        return get_devices_names(self.live_listen_props.include_output_devices.get())

    def _refresh_input_devices(self):
        current_selection = self.live_listen_props.selected_live_device.get()
        new_values = self._get_input_devices()
        self.audio_device_dropdown['values'] = new_values

        if current_selection in new_values:
            self.live_listen_props.selected_live_device.set(current_selection)
        else:
            self.live_listen_props.selected_live_device.set('')

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
