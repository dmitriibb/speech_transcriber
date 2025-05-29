from datetime import datetime

class Logger:
    def __init__(self):
        self._log_func = None
        self._show_error_func = None

    def set_log_func(self, log_func):
        self._log_func = log_func

    def set_show_error_func(self, show_error_func):
        self._show_error_func = show_error_func

    def log(self, message: str):
        current_time = datetime.now().strftime("%M:%S")
        formatted_message = f"{current_time}: {message}"
        print(formatted_message)
        if self._log_func is not None:
            self._log_func(formatted_message)

    def error(self, message: str):
        self.log(f"ERROR: {message}")

    def show_error(self, message: str):
        self.error(message)
        if self._show_error_func is not None:
            self._show_error_func(message)


logger = Logger()