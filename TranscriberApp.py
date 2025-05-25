import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import os
import queue

import pyaudio
import wave
import time

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

from speech_recognition import Recognizer, AudioFile

class TranscriberApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Local Audio Transcriber")

        self.use_ai = tk.BooleanVar()
        self.output_dir = tk.StringVar()
        self.is_transcribing = False
        self.audio_queue = queue.Queue()
        self.audio_sources = []
        self.selected_source_name = tk.StringVar()

        self.pyaudio_instance = pyaudio.PyAudio()
        self.get_audio_sources()
        self.build_gui()

    def get_audio_sources(self):
        self.audio_sources.clear()
        for i in range(self.pyaudio_instance.get_device_count()):
            info = self.pyaudio_instance.get_device_info_by_index(i)
            if info.get('maxInputChannels') > 0:
                self.audio_sources.append((i, info.get('name')))
        if self.audio_sources:
            self.selected_source_name.set(self.audio_sources[0][1])

    def build_gui(self):
        tk.Label(self.root, text="Audio Input Source:").pack()
        source_names = [name for idx, name in self.audio_sources]
        self.input_menu = tk.OptionMenu(self.root, self.selected_source_name, *source_names)
        self.input_menu.pack()

        tk.Label(self.root, text="Output Directory:").pack()
        tk.Entry(self.root, textvariable=self.output_dir, width=50).pack()
        tk.Button(self.root, text="Choose Folder", command=self.choose_directory).pack(pady=5)

        tk.Checkbutton(self.root, text="Use AI (Whisper)", variable=self.use_ai).pack()

        self.start_button = tk.Button(self.root, text="Start Transcription", command=self.start_transcription)
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(self.root, text="Stop", command=self.stop_transcription, state=tk.DISABLED)
        self.stop_button.pack()


    def update_source_label(self, *args):
        index = self.selected_source_index.get()
        if 0 <= index < len(self.audio_sources):
            self.source_labels.config(text=self.audio_sources[index][1])

    def choose_directory(self):
        current_dir = os.path.dirname(os.path.realpath(__file__))
        directory = filedialog.askdirectory(initialdir=current_dir)
        if directory:
            self.output_dir.set(directory)

    def start_transcription(self):
        if not self.output_dir.get():
            messagebox.showwarning("Missing Info", "Please choose an output directory.")
            return

        self.is_transcribing = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

        threading.Thread(target=self.transcription_loop).start()

    def stop_transcription(self):
        self.is_transcribing = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def transcription_loop(self):

        output_path = os.path.join(self.output_dir.get(), "transcription.txt")

        if self.use_ai.get():
            if not WHISPER_AVAILABLE:
                messagebox.showerror("Error", "Whisper not installed.")
                return
            model = whisper.load_model("base")
        else:
            recognizer = Recognizer()

        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 16000
        CHUNK = 1024
        RECORD_SECONDS = 5
        audio = pyaudio.PyAudio()

        stream = audio.open(format=FORMAT, channels=CHANNELS,
                            rate=RATE, input=True,
                            frames_per_buffer=CHUNK)

        with open(output_path, "w", encoding="utf-8") as f:
            while self.is_transcribing:
                frames = []
                for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    data = stream.read(CHUNK)
                    frames.append(data)

                temp_filename = "temp.wav"
                wf = wave.open(temp_filename, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
                wf.close()

                try:
                    if self.use_ai.get():
                        result = model.transcribe(temp_filename)
                        f.write(result["text"] + "\n")
                    else:
                        with AudioFile(temp_filename) as source:
                            audio_data = recognizer.record(source)
                            text = recognizer.recognize_sphinx(audio_data)
                            f.write(text + "\n")
                    f.flush()
                except Exception as e:
                    f.write(f"[ERROR] {e}\n")
                    f.flush()

        stream.stop_stream()
        stream.close()
        audio.terminate()

        # if os.path.exists("temp.wav"):
        #     os.remove("temp.wav")

if __name__ == "__main__":
    root = tk.Tk()
    app = TranscriberApp(root)
    root.mainloop()
