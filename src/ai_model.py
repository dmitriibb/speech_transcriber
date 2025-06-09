import torch
import whisper

from logger import logger


class AiModel:
    def __init__(self, model_name: str, tmp_directory: str):
        self._model_name = model_name
        self._tmp_directory = tmp_directory
        self._whisper_model = None

    def load(self):
        self._load_whisper()

    def _load_whisper(self):
        if self._whisper_model is None:
            if self._model_name is None:
                raise Exception("AI model name is not configured")
            cuda = torch.cuda.is_available()
            logger.log(f"AiModel: loading Whisper model '{self._model_name}', (cuda: {cuda})...")
            self._whisper_model = whisper.load_model(
                name=self._model_name,
                download_root=self._tmp_directory
            )
        logger.log(f"AiModel: Whisper model loaded")

    def transcribe(self, data):
        return self._whisper_model.transcribe(data)

