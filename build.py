import os
import subprocess
import sys
import shutil

import PyInstaller.__main__
from pathlib import Path
import site

def install_build_requirements():
    print("Installing build requirements...")
    # First uninstall PyInstaller to ensure clean state
    subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "pyinstaller"])
    # Install specific version of PyInstaller
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "setuptools", "wheel"])
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller==5.13.2"])
    # Install application requirements
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements-build-exe.txt"])

def cleanup():
    print("Cleaning up previous builds...")
    dirs_to_remove = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    for spec_file in ['speech_transcriber.spec']:
        if os.path.exists(spec_file):
            os.remove(spec_file)
    # Clean all __pycache__ directories recursively
    for root, dirs, files in os.walk('.'):
        for d in dirs:
            if d == '__pycache__':
                shutil.rmtree(os.path.join(root, d))

def build_exe():
    print("Building speech_transcriber.exe...")
    
    # Get the absolute path to the src directory
    src_dir = os.path.abspath('src')
    
    # Create a temporary directory for the build
    if not os.path.exists('build_tmp'):
        os.makedirs('build_tmp')
    
    # Copy all source files to build_tmp
    for file in os.listdir(src_dir):
        if file.endswith('.py'):
            shutil.copy2(os.path.join(src_dir, file), 'build_tmp')
    
    # Change to build_tmp directory
    os.chdir('build_tmp')
    
    # Build command with additional options for better compatibility
    cmd = [
        'pyinstaller',
        '--noconfirm',
        '--onefile',
        '--windowed',
        '--clean',
        '--log-level=DEBUG',
        '--name', 'speech_transcriber',
        '--icon=../src/assets/icon.ico' if os.path.exists('../src/assets/icon.ico') else '',
        # Add hidden imports that might be needed
        '--hidden-import=queue',
        '--hidden-import=pynput.keyboard._win32',
        '--hidden-import=pynput.mouse._win32',
        '--hidden-import=numpy',
        '--hidden-import=sounddevice',
        '--hidden-import=pyaudio',
        '--hidden-import=pocketsphinx',
        '--hidden-import=openai-whisper',
        '--hidden-import=pydub',
        '--hidden-import=soundfile',
        '--collect-all', 'whisper',
        '--collect-all', 'sounddevice',
        '--collect-all', 'pyaudio',
        '--collect-all', 'pocketsphinx',
        'main.py'
    ]
    
    # Remove empty elements
    cmd = [x for x in cmd if x]
    
    try:
        # Execute the build with output displayed
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        # Print output in real-time
        for line in process.stdout:
            print(line, end='')
            
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)
            
        # Move the built executable back to the dist directory
        if not os.path.exists('../dist'):
            os.makedirs('../dist')
        shutil.move('dist/speech_transcriber.exe', '../dist/')
        
        # Clean up build_tmp directory
        os.chdir('..')
        shutil.rmtree('build_tmp')
            
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed with return code: {e.returncode}")
        raise

def main():
    cleanup()
    # Get the absolute path of the scriptAdd commentMore actions
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
        '--collect-all=whisper',
        '--collect-all=sounddevice',
        '--collect-all=pocketsphinx',
        '--collect-all=speech_recognition',
        '--collect-all=numpy',
        '--collect-all=pyaudio',
        '--clean',
    ]

    # Run PyInstaller
    PyInstaller.__main__.run(args)

if __name__ == "__main__":
    main() 