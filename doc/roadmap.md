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
Status: TODO

Goal: human speech transcription with python libraries

Description: In the Transcriber implement 'def _dummy_transcribe(self, chunk_audio) -> str:' method. Use python libraries.
Import them if needed, but these libraries should use any external AI models

### Iteration 3
Status: TODO
