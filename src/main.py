import tkinter as tk
from enum import Enum
from tkinter import ttk, filedialog, messagebox
import sounddevice as sd
import os
import threading
import whisper

from urllib3.filepost import writer

from audio_listener import AudioListener
from file_listener import FileListener
from src.audio_devices import get_devices_names
from src.configs import OutputConfig, TranscriberConfig, AudioListenerConfig
from src.constants import *
from src.gui_renderer import MainProps, LiveListenProps, FileListenProps, OutputProps, RecognizerProps, StatusProps, LogsProps, GuiRenderer
from src.actions import TranscriberActions
from src.gui_utils import get_available_models, get_downloaded_models, format_model_name
from src.logger import Logger, logger
from src.model import InputMode
from transcriber import Transcriber
from output_writer import OutputWriter


class TranscriberApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Speech Transcriber")
        self.root.geometry("600x700")
        
        # State variables
        self.logger = Logger()
        self.listener : AudioListener = None
        self.file_listener : FileListener = None

        # Initialize base directories
        base_directory = os.path.dirname(os.path.abspath(__file__))
        head, tail = os.path.split(base_directory)
        if tail == "src":
            output_directory = os.path.join(head, "output")
            tmp_directory = os.path.join(head, "tmp")
        else:
            output_directory = base_directory
            tmp_directory = os.path.join(base_directory, "tmp")

        # Initialize props
        self.main_props = MainProps(InputMode.LIVE)
        self.live_listen_props = LiveListenProps()
        self.file_listen_props = FileListenProps()
        self.output_props = OutputProps(output_directory, tmp_directory)
        self.recognizer_props = RecognizerProps(recogniserGoogleCloud)
        self.status_props = StatusProps(statusReady)
        self.logs_props = LogsProps()

        # Initialize actions
        self.actions = TranscriberActions()
        self.actions.start_transcribing = self._start_transcribing
        self.actions.stop_transcribing = self._stop_transcribing
        self.actions.toggle_transcription = self._toggle_transcription
        self.actions.choose_directory = self._choose_directory
        self.actions.choose_tmp_directory = self._choose_tmp_directory
        self.actions.toggle_ai = self._toggle_ai
        self.actions.download_model = self._download_model
        self.actions.on_ai_model_select = self._on_ai_model_select

        # Initialize GUI
        self.gui = GuiRenderer(
            root=self.root,
            main_props=self.main_props,
            live_listen_props=self.live_listen_props,
            file_listen_props=self.file_listen_props,
            output_props=self.output_props,
            recognizer_props=self.recognizer_props,
            status_props=self.status_props,
            logs_props=self.logs_props,
            actions=self.actions
        )

        # Setup logging
        def log(message):
            self.logs_props.logs_text.configure(state="normal")
            self.logs_props.logs_text.insert("end", f"{message}\n")
            self.logs_props.logs_text.see("end")  # Auto-scroll to the bottom
            self.logs_props.logs_text.configure(state="disabled")
        logger.set_log_func(log)

        def show_error(message):
            tk.messagebox.showerror("Error", message)
        logger.set_show_error_func(show_error)

        # Render GUI
        self.gui.render_all()

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
            self._update_ai_models_dropdown() # Refresh models status
            
    def _toggle_transcription(self):
        if self.status_props.transcribing:
            self._stop_transcribing()
        else:
            self._start_transcribing()

    def _start_transcribing(self):
        transcribing_file = self.main_props.input_mode.get() == InputMode.FILE.value
        if transcribing_file and not self.recognizer_props.use_ai.get():
            logger.show_error("File transcribing is only available with AI")
            return

        try:
            output_config = OutputConfig(self.output_props.output_directory.get())

            output_writer = OutputWriter(output_config, self.set_initial_state)
            output_writer.start_new_file()

            model_name = self.recognizer_props.selected_ai_model.get().split(" - ")[0] if self.recognizer_props.use_ai.get() else None
            transcriber_config = TranscriberConfig(
                recogniser_name=self.recognizer_props.selected_recognizer.get(),
                tmp_directory=self.output_props.tmp_directory.get(),
                use_ai=self.recognizer_props.use_ai.get(),
                model_name=model_name,
            )
            transcriber = Transcriber(output_writer, transcriber_config)
            transcriber.init()

            if transcribing_file:
                self.listener = FileListener(transcriber)
                self.listener.set_input_file(self.file_listen_props.selected_file.get())
            else:
                audio_config = AudioListenerConfig(
                    audio_device_name=self.live_listen_props.selected_live_device.get(),
                    chunk_duration=int(self.recognizer_props.chunk_duration.get())
                )
                self.listener = AudioListener(transcriber, audio_config)

            self.listener.start()
            self.status_props.status.set(statusTranscribing)
            self.status_props.transcribing = True
            self.status_props.start_button.configure(text="Stop")
        except Exception as e:
            logger.show_error(f"Failed to start transcription: {str(e)}")
            self.set_initial_state()

    def _stop_transcribing(self):
        self.status_props.status.set(statusFinishing)
        if self.listener:
            self.listener.stop()

    def set_initial_state(self):
        self.listener = None
        self.status_props.transcribing = False
        self.status_props.status.set(statusReady)
        self.status_props.start_button.configure(text="Start")

    def log_all_devices(self):
        self.logger.log("all available devices:")
        hostapis = sd.query_hostapis()
        for i, h in enumerate(hostapis):
            self.logger.log(f"{i}: {h['name']}")
        for i, dev in enumerate(sd.query_devices()):
            self.logger.log(f"{i}: {dev['name']} ({dev['hostapi']})")

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

def main():
    root = tk.Tk()
    app = TranscriberApp(root)
    root.mainloop()


if __name__ == "__main__":
    main() 