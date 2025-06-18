### Install pyenv 

1. 
    ```sudo apt update
    sudo apt install -y make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
    libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \
    libffi-dev liblzma-dev git
    ```
2. 
    ```
    curl https://pyenv.run | bash
    ```
3. Add the following to your shell startup file (~/.bashrc, ~/.zshrc, or ~/.profile):
    ```
   export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"
    ```
4. After editing, reload your shell:
   ```
    exec "$SHELL"
    ```
5. Install Python 3.10 Using Pyenv
    ```
   pyenv install 3.10.13
   ```
6. In the project directory run
   ```
   pyenv local 3.10.13
   python -m venv venv
   source venv/bin/activate
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   sudo apt install portaudio19-dev
   pip install -r requirements.txt
   sudo apt install ffmpeg. Verify the installation by checking the version with ffmpeg -version
   ```
   
7. Run the app with
```bash
python src/main.py
```