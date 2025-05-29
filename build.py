import PyInstaller.__main__
import os
import sys
from pathlib import Path
import site

def main():
    # Get the absolute path of the script
    script_path = os.path.dirname(os.path.abspath(__file__))
    
    # Define the path to main.py
    main_path = os.path.join(script_path, 'src', 'main.py')
    
    # Get site-packages directory
    site_packages = site.getsitepackages()[0]
    
    # Define PyInstaller arguments
    args = [
        main_path,
        '--onefile',
        '--windowed',
        '--name=SpeechTranscriber',
        '--add-data=src;src',
        '--hidden-import=queue',
        '--hidden-import=pocketsphinx',
        '--hidden-import=speech_recognition',
        '--hidden-import=sounddevice',
        '--hidden-import=numpy',
        '--hidden-import=pyaudio',
        '--collect-all=sounddevice',
        '--collect-all=pocketsphinx',
        '--collect-all=speech_recognition',
        '--collect-all=numpy',
        '--collect-all=pyaudio',
        '--clean',
    ]
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)

if __name__ == '__main__':
    main() 