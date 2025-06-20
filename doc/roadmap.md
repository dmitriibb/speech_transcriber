# Context:
We are building an application for human speech transcription.
## Application requirements:
1) The app should run locally on Windows PC
2) The app should be written in Python
3) The app should have simple GUI with
   1) dropdown menu with all possible audio input sources from the system
   2) file directory choose field for output txt 
   3) "use AI" toggle
   4) Start/Stop transcription button

4) When click "Start" button the app should:
   - start to listen to selected audio input sources
   - take human speach from it and transcribe it into text 
   - write the text into the output file
5) When click "Stop" button the app should:
   - stop listening input sources

6) If "use AI" toggle is disabled - then the app should use some standard / simple / small libraries for transcription
7) If "use AI" toggle is enabled - then the app should use AI for transcription.
   - The AI model should run locally on the PC
   - The AI should be built in into te application (meaning - user doesn't need to install the AI model manually)
8) All transcriptions should be processed locally - online tools, API or online AI models are not allowed

## The development is split by iterations. We implement them 1 by 1

### Iteration 0
Status: Done

Goal: Running application with working GUI. No transcription logic should be implemented yet

Description: Implement simple python GUI application with next elements:

- Input source dropdown
  - when click on dropdown - user should see all available input sources of the system (their names)
  - when user select one of them - we save the selected option in the memory
- Output directory
  - currently selected directory should be displayed in the text field
  - on the right side of the text field should be a button "choose". When click on the button - we should see directory selection window. 
This window should be opened with predefined path = directory of the application
- Start button
  - when click - set in memory boolean "transcribing" = True and change "Start" button to "Stop" button
- Stop button
  - when click - set in memory boolean "transcribing" = False and change "Stop" button to "Start" button

### Iteration 1
Status: Done

Goal: Implement basic audio listening, transcribing and output files writing

Description: Implement next components

- AudioListener
  - When transcribing = True - listener takes audio from selected audio source and every 5 seconds sends a new chunk of audio into the Transcriber
- Transcriber
  - has 1 method transcribe(self, chunk_audio)
  - The method accepts audio chunk from Listener, applies dummy_transcribe() function on th chunk, and sends the result of that function to the OutputWriter
  - transcribe(self, chunk_audio) is non-blocking. Meaning - when AudioListener sends a new chunk into Transcriber.transcribe(self, chunk_audio),
the AudioListener doesn't wait transcribe function to finish
  - dummy_transcribe() returns string "chunk: {chunk number}, size: {chunk size in bytes} bytes"
- OutputWriter
  - When Start button is clicked and transcribing boolean changed from False to True - create a new file "transcription-{N}.txt" in the Output directory
  - If Output directory already has files like "transcription-1.txt" and "transcription-2.txt", then the new file should be "transcription-3.txt"
  - Takes chunk_transcribed string and appends in to the current output file

### Iteration 2
Status: Done

Goal: human speech transcription with python libraries

Description: In the Transcriber implement 'def _dummy_transcribe(self, chunk_audio) -> str:' method. Use python libraries.
Import them if needed, but these libraries should use any external AI models

### Iteration 3
Status: Done

Goal: add AI model and use  it for transcribing

Description: we need to implement next features

- In the GUI under recogniser_widget add new section AI. In this section we should have 1 checkbox / toggle "Enable". This toggle should change app variable "ai_enabled"
- if "ai_enabled" = True, then in the Transcriber we should use AI model regardless of selected transcriber
- For speech recognition we need to use AI model Whisper 

### Iteration 4
Status: Done

Goal: add support to transcribe a single mp3 file

Description: need to add next features
- at the top of the GUI add toggle or switch between transcribe "live" and "file"
- if "live" is selected - then existing input sourse is enabled and currently implemented logic remains the same
- if "file" is selected:
  - disable "input sourse" dropdown
  - enable "input file" field - this should be a new file choose field and button
  - Create a new class FileListener (create a new file file_listener.py) for that. 
  - In the existing flow just use this FileListener instead of AudioListener
  - FileListener for uses only AI and feeds the whole file into AI model

### Iteration 5
Status: Done

Goal: we need to have opportunity to choose Whisper model

Description: add next features
- Move "Use AI" checkbox into the new section called "AI section"
- If "Use AI" is checked - in the "Ai section" display a dropdown with all available Whisper models ("base", "small.en" etc..)
- Items in the dropdown should look like [model_name - downloaded_status] Example: "base - downloaded", "small.en - to download"
- Downloaded models should be stored in the tmp_directory. So we can always see which one are downloaded already
- If user selects option with "to download" - then we download that model into the tmp_directory

### Iteration 6
Status: Done

Goal: refactor UI to support multiple audio listeners at once. 
That will allow us to listen to multiple people at once and distinguish their speech in the transcribed text later

Description: refactor UI and implement next features
- In the GUI live_frame we should have [Add] button. When the button is clicked - the new live input line should be added
- Structure of the live input line:
  - [-] button - removes the current line
  - [audio devices dropdown] - we already have this field implemented, but only for 1 device 
  - [name] - name of the speaker. short text input. Default: A, B, C, D letter for each new line
  - [record checkbox] - if true - then in the AudioListener we should record this device and save the recording into hte output directory
  - [transcribe checkbox] - if true - then AudioListener should transcribe this device
- Desired result example:
  - we have 2 audio devices selected: `[mic 1][A][record=True][transcribe=True]` and `[mic 2][B][record=True][transcribe=True]`
  - When we click start 2 Transcribers and 2 AudioListeners will be created - one for each input device
  - In the output directory we will have 2 audio record: `rec-1-A.wav`, `rec-1-B.wav`
  - In the output directory we will have 1 text transcription: `transcription-1.txt`. But in that file we will have 2 transcriptions like:
    - A: Hello
    - B: Hello indeed, how are you?
    - A: I'm good, thanks
    - B: glad to hear

### Iteration 7
Status: TODO

Goal: Be able to build the application into speach_transcriber.exe file

Description:
- Write some script, which can be executed on my Windows machine. This script should build this application into the one .exe file
- We use Python 3.10.0
- Use requirements-build-exe.txt file for dependencies management


### Iteration 8
Status: TODO