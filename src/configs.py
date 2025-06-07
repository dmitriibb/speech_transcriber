from dataclasses import dataclass
from typing import Optional

from model import AudioInputLine


@dataclass
class OutputConfig:
    output_directory: str


@dataclass
class TranscriberConfig:
    recogniser_name: str
    tmp_directory: str
    use_ai: bool
    model_name: Optional[str]
    transcription_index: int
    speaker_name: str


@dataclass
class AudioListenerConfig:
    input_line: AudioInputLine
    chunk_duration: int
    transcription_index: int