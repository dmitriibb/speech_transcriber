import tkinter as tk
import os
import whisper

from audio_listener import AudioListener
from file_listener import FileListener
from configs import OutputConfig, TranscriberConfig, AudioListenerConfig
from constants import *
from gui_renderer import MainProps, LiveListenProps, FileListenProps, OutputProps, RecognizerProps, StatusProps, LogsProps, GuiRenderer
from actions import TranscriberActions
from logger import Logger, logger
from model import InputMode, ListenerBase
from transcriber import Transcriber
from output_writer import OutputWriter


class TranscriberApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Speech Transcriber")
        self.root.geometry("700x700")
        
        # State variables
        self.logger = Logger()
        self.listeners = []

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

    def _start_transcribing(self):
        transcribing_file = self.main_props.input_mode.get() == InputMode.FILE.value
        if transcribing_file and not self.recognizer_props.use_ai.get():
            logger.show_error("File transcribing is only available with AI")
            return

        try:
            output_config = OutputConfig(self.output_props.output_directory.get())
            output_writer = OutputWriter(output_config, self.set_initial_state)
            transcription_index = output_writer.start_new_file()

            model_name = self.recognizer_props.selected_ai_model.get().split(" - ")[0] if self.recognizer_props.use_ai.get() else None

            self.listeners = []

            if transcribing_file:
                transcriber_config = TranscriberConfig(
                    recogniser_name=self.recognizer_props.selected_recognizer.get(),
                    tmp_directory=self.output_props.tmp_directory.get(),
                    use_ai=self.recognizer_props.use_ai.get(),
                    model_name=model_name,
                    transcription_index=transcription_index,
                    speaker_name=""
                )
                transcriber = Transcriber(output_writer, transcriber_config)
                transcriber.init()

                listener = FileListener(transcriber)
                listener.set_input_file(self.file_listen_props.selected_file.get())
                self.listeners.append(listener)
            else:
                # Create listeners for each enabled input line
                for input_line in self.live_listen_props.audio_input_lines:
                    transcriber_config = TranscriberConfig(
                        recogniser_name=self.recognizer_props.selected_recognizer.get(),
                        tmp_directory=self.output_props.tmp_directory.get(),
                        use_ai=self.recognizer_props.use_ai.get(),
                        model_name=model_name,
                        transcription_index=transcription_index,
                        speaker_name=input_line.speaker_name
                    )
                    transcriber = Transcriber(output_writer, transcriber_config)
                    transcriber.init()

                    if input_line.record or input_line.transcribe:
                        audio_config = AudioListenerConfig(
                            input_line=input_line,
                            chunk_duration=int(self.recognizer_props.chunk_duration.get()),
                            transcription_index=transcription_index
                        )
                        listener = AudioListener(transcriber, audio_config)
                        self.listeners.append(listener)

            for listener in self.listeners:
                listener.start()

            self.status_props.status.set(statusTranscribing)
            self.status_props.transcribing = True
            self.status_props.start_button.configure(text="Stop")
        except Exception as e:
            logger.show_error(f"Failed to start transcription: {str(e)}")
            self.set_initial_state()

    def _stop_transcribing(self):
        self.status_props.status.set(statusFinishing)
        for listener in self.listeners:
            listener.stop()
        self.listeners = []

    def set_initial_state(self):
        self.listeners = []
        self.status_props.transcribing = False
        self.status_props.status.set(statusReady)
        self.status_props.start_button.configure(text="Start")

def main():
    root = tk.Tk()
    app = TranscriberApp(root)
    root.mainloop()


if __name__ == "__main__":
    main() 