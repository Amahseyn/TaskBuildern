import logging
import sys
from typing import Optional, List

class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG":    "\033[36m",
        "INFO":     "\033[32m",
        "WARNING":  "\033[33m",
        "ERROR":    "\033[31m",
        "CRITICAL": "\033[35m\033[1m",
    }
    RESET = "\033[0m"
    BOLD  = "\033[1m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{self.BOLD}{record.levelname:<8}{self.RESET}"
        return super().format(record)

def setup_logging(verbose: bool = False, log_file: Optional[str] = None) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    fmt   = "%(asctime)s [%(levelname)s] %(message)s"
    datefmt = "%H:%M:%S"

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(ColorFormatter(fmt, datefmt))

    handlers: List[logging.Handler] = [console]
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter(fmt, datefmt))
        handlers.append(fh)

    logging.basicConfig(level=level, handlers=handlers, force=True)
    return logging.getLogger("extraction")

log = logging.getLogger("extraction")
