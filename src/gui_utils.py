import os
import whisper

def get_available_models():
    """Returns a list of available whisper models."""
    return whisper.available_models()

def get_downloaded_models(tmp_directory):
    """
    Returns a list of downloaded models by checking the tmp_directory.
    Models are saved with a .pt extension.
    """
    downloaded = []
    if not os.path.exists(tmp_directory):
        return downloaded
    
    for file in os.listdir(tmp_directory):
        if file.endswith(".pt"):
            downloaded.append(os.path.splitext(file)[0])
    return downloaded

def format_model_name(model, downloaded_models):
    """Formats the model name for the dropdown."""
    status = "downloaded" if model in downloaded_models else "to download"
    return f"{model} - {status}" 