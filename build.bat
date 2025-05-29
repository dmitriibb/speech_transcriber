@echo off
echo Starting build process...

call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64


REM Store the current directory
set INIT_DIR=%CD%

REM Try to find Python 3.10
set PYTHON_310=
for %%I in (
    "%ProgramFiles%\Python310\python.exe"
    "%ProgramFiles(x86)%\Python310\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
) do (
    if exist %%I (
        set PYTHON_310=%%I
        goto found_python
    )
)

:not_found_python
echo Error: Could not find Python 3.10 installation!
echo Please ensure Python 3.10 is installed in one of these locations:
echo - %ProgramFiles%\Python310
echo - %ProgramFiles(x86)%\Python310
echo - %LocalAppData%\Programs\Python\Python310
goto error

:found_python
echo Found Python 3.10: %PYTHON_310%

echo Cleaning previous builds...
call clean.bat

echo Creating virtual environment...
%PYTHON_310% -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo Error creating virtual environment!
    goto error
)

call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo Error activating virtual environment!
    goto error
)

echo Installing base requirements...
python -m pip install --upgrade pip
pip install wheel setuptools

echo Installing numpy first...
pip install numpy==1.24.3
if %ERRORLEVEL% NEQ 0 (
    echo Error installing numpy!
    goto error
)

echo Installing PyAudio from wheel...
if exist "wheels\pymol-3.1.0-cp310-cp310-win_amd64.whl" (
    pip install "wheels\pymol-3.1.0-cp310-cp310-win_amd64.whl"
) else if exist "wheels\PyAudio-0.2.11-cp310-cp310-win32.whl" (
    pip install "wheels\PyAudio-0.2.11-cp310-cp310-win32.whl"
) else (
    echo Error: PyAudio wheel not found in wheels directory!
    echo Please download the appropriate wheel from:
    echo https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
    echo and place it in the wheels directory.
    goto error
)

echo Installing sounddevice...
pip install sounddevice==0.4.6
if %ERRORLEVEL% NEQ 0 (
    echo Error installing sounddevice!
    goto error
)

echo Installing other requirements...
pip install SpeechRecognition==3.10.0 pocketsphinx==5.0.0 urllib3==2.0.7
if %ERRORLEVEL% NEQ 0 (
    echo Error installing speech recognition packages!
    goto error
)

echo Installing PyInstaller...
pip install pyinstaller==5.13.2
if %ERRORLEVEL% NEQ 0 (
    echo Error installing PyInstaller!
    goto error
)

echo Building executable...
python build.py
if %ERRORLEVEL% NEQ 0 (
    echo Error during PyInstaller build!
    goto error
)

echo Deactivating virtual environment...
deactivate

echo Build completed successfully!
echo The executable can be found in the dist folder.
goto end

:error
echo.
echo Build failed! See error messages above.
echo.
echo If you're having issues with PyAudio installation:
echo 1. Download the appropriate wheel from:
echo    https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
echo 2. Place it in the 'wheels' directory
echo.
echo If you're having issues with sounddevice:
echo 1. Make sure you have the Microsoft Visual C++ Redistributable installed
echo 2. Try running: pip install sounddevice --no-cache-dir
echo.

:end
cd %INIT_DIR%
echo.
echo Press any key to exit...
pause > nul 