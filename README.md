# Speech Transcriber

A local Windows application for transcribing speech to text.

## Setup Instructions
### Windows
1. Make sure you have Python 3.10 installed
   1. [go here](https://www.python.org/downloads/release/python-3100/) and choose `Windows installer (64-bit)`
   2. At the end of the installation make sure you check something like `Add Python to the PATH` 
2. Install ffmpeg 
   1. Run cmd or PowerShell as Administrator and execute the installation script from [choco](https://community.chocolatey.org/)
   2. Run cmd or PowerShell as Administrator and execute the next command `choco install ffmpeg`
3. run `INSTALL.bat`, wait until it finished and closed the cmd window
   - If you have Nvidia graphic card - you can run `INSTALL-for-nvidia-gpu.bat`. This will allow AI to run on GPU instead of CPU

For getting updates run `GET-UPDATE.bat`

### Ubuntu
Read [this](run_in_ubuntu.md)

## Running the Application

### Windows
- run `START.bat`
  - This will open the app and a new cmd. Don't close the cmd, but you can see some additional logs there

### Ubuntu
- Run the app with
    ```bash
    python src/main.py
    ```

## Features
- Live transcription
  - Choose 1 or multiple input devices to listen.
  - You try to can check `include output devices`. But capturing audio from output devices most likely won't work
  - Give a name to each input like `speaker 1` and `speaker 2`. So you can distinguish them in the transcription.txt
  - Check `record` - this will record the audio from the device and save it in the output directory
  - Check `transcribe` - this will transcribe the audio from the device and save it into the transcription-n.txt file in the output directory
  - You can choose `Speech recognition`:
    - dummy - does nothing
    - sphynx - local (on your PC). But don't expect the good result
    - google cloud - sends your audio to google web service
    - If check "Use AI" - selected `Speech recognition` will be ignored 
  - Set `Chunk duration (sec):` - In Live transcription audio is being processed by chunks. The app can't distinguish when a speaker finished his sentence.
Therefore the app just transcribes each 5 seconds as a separate chunk. This can cause the issue when 1 chunk ends in the middle of the word.
- File transcription
  - Choose 1 file. By default file browser filters only audio files. But you can opt for `all file types` in the right bottom corner
  - File transcription ignores selected `Speech recognition` and always uses AI
  - Transcribing 1 hour speech file with `base.en` model takes about 10 minutes on average mobile CPU
- AI
  - The app uses local `openai-whisper` model
  - You need to choose the size of the model. The selected model will be downloaded only 1 time and stored in the selected tmp directory
  - |  Size  | Parameters | English-only model | Multilingual model | Required VRAM |
    |:------:|:----------:|:------------------:|:------------------:|:-------------:|
    |  tiny  |    39 M    |     `tiny.en`      |       `tiny`       |     ~1 GB     |
    |  base  |    74 M    |     `base.en`      |       `base`       |     ~1 GB     |
    | small  |   244 M    |     `small.en`     |      `small`       |     ~2 GB     |
    | medium |   769 M    |    `medium.en`     |      `medium`      |     ~5 GB     |
    | large  |   1550 M   |        N/A         |      `large`       |    ~10 GB     |
    | turbo  |   809 M    |        N/A         |      `turbo`       |     ~6 GB     | 
  - Once selected model is downloaded - you can click `Start`
  - If `Live transcription` is selected and multiple input devices are selected - this will upload multiple AI models in your RAM.


