# logging_config.py
import logging
import sys
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
from colorama import Fore, Style, init as colorama_init

colorama_init()

# Create a log formatter with color support
class ColorFormatter(logging.Formatter):
    def format(self, record):
        level = record.levelname
        color = {
            'DEBUG': Fore.BLUE,
            'INFO': Fore.GREEN,
            'WARNING': Fore.YELLOW,
            'ERROR': Fore.RED,
            'CRITICAL': Fore.MAGENTA
        }.get(level, Fore.WHITE)

        record.levelname = f"{color}{level}{Style.RESET_ALL}"
        return super().format(record)

def setup_logging(log_file="logs/combined.log"):
    log_queue = Queue()
    queue_handler = QueueHandler(log_queue)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColorFormatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()  # prevent duplication on re-runs
    root_logger.addHandler(queue_handler)

    listener = QueueListener(log_queue, console_handler, file_handler)
    listener.start()

